"""
Durable review-triage agent: LangGraph on Diagrid Catalyst.

One container, outbound-only networking. Fetches Google Places reviews,
classifies each with an LLM, routes it to an owning team, and runs each
review as a Catalyst durable workflow so a crash mid-run resumes at the
exact failed step instead of re-billing the LLM call.

Two ways to hand a review to the workflow (PASS_REVIEW_BY env var):
  reference (default): workflow input is {place_id, review_id}; the classify
      activity fetches the text itself. Catalyst's workflow history then holds
      only identifiers and classifications, never third-party review text.
  text: workflow input carries the review text; simpler, and the Catalyst
      console shows the full state, which is useful for demos with sample data.

Verified against diagrid==0.4.3 (Aug 2026). See README.md for setup.
"""
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypedDict

import httpx
from fastapi import FastAPI, HTTPException
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from diagrid.agent.langgraph import DaprWorkflowGraphRunner

PLACES = "https://places.googleapis.com/v1/places"
SAMPLE_FILE = Path(__file__).with_name("sample_reviews.json")

# theme -> owning team. Swap for your org's routing table.
ROUTES = {
    "service": "store-ops@corp.example",
    "product": "merchandising@corp.example",
    "cleanliness": "facilities@corp.example",
    "pricing": "pricing@corp.example",
}
FALLBACK_OWNER = "cx-team@corp.example"


PASS_REVIEW_BY = os.environ.get("PASS_REVIEW_BY", "reference").lower()  # reference | text


class TriageState(TypedDict, total=False):
    place_id: str
    review_id: str
    review: str            # only populated in PASS_REVIEW_BY=text mode
    classification: dict
    owner: str


def _sample_reviews() -> list[dict]:
    return json.loads(SAMPLE_FILE.read_text())


def _places_reviews_sync(place_id: str) -> list[dict]:
    """Synchronous Places fetch (used inside the classify activity, which runs in a worker thread)."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set (or use place_id 'sample')")
    r = httpx.get(
        f"{PLACES}/{place_id}",
        headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "reviews"},
        timeout=20,
    )
    r.raise_for_status()
    return [
        {"id": v.get("name", ""), "rating": v.get("rating"),
         "text": (v.get("text") or {}).get("text", "")}
        for v in r.json().get("reviews", [])
    ]


def list_reviews(place_id: str) -> list[dict]:
    """Return [{"id", "rating", "text"}] for a place. 'sample' = bundled synthetic reviews."""
    return _sample_reviews() if place_id == "sample" else _places_reviews_sync(place_id)


def review_text_for(place_id: str, review_id: str) -> str:
    """Resolve a review reference to its text; used only inside the classify activity."""
    for v in list_reviews(place_id):
        if v.get("id") == review_id:
            return f"Rating {v.get('rating')}/5: {v.get('text', '')}"
    raise RuntimeError(f"review {review_id!r} not found for place {place_id!r}")


llm = ChatAnthropic(model=os.environ.get("LLM_MODEL", "claude-sonnet-4-6"), temperature=0)


def classify(state: TriageState) -> TriageState:
    """Step 1 (durable activity): LLM classifies the review.

    In reference mode the text is fetched here and used locally; it is never
    returned into graph state, so it never lands in Catalyst's workflow history.
    """
    review = state.get("review") or review_text_for(state["place_id"], state["review_id"])
    prompt = (
        "Classify this customer review. Return ONLY strict JSON with keys: "
        "sentiment (positive|neutral|negative), "
        "theme (service|product|cleanliness|pricing|other), "
        "urgency (act-now|monitor|none), "
        "summary (one sentence).\n\nReview:\n" + review
    )
    msg = llm.invoke(prompt)
    text = msg.text.strip()
    # tolerate ```json fences
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):text.rfind("}") + 1]
    return {"classification": json.loads(text)}


def route(state: TriageState) -> TriageState:
    """Step 2 (durable activity): map theme to owning team.

    CRASH_TEST_DELAY (seconds, default 0) widens the window between the
    completed classify activity and this one so you can `kill -9` the process
    mid-workflow and watch Catalyst resume here without re-running the LLM.
    """
    delay = float(os.environ.get("CRASH_TEST_DELAY", "0"))
    if delay:
        print(f"  [CRASH-TEST] route sleeping {delay:.0f}s: kill -9 the process now", flush=True)
        time.sleep(delay)
    theme = state["classification"].get("theme", "other")
    return {"owner": ROUTES.get(theme, FALLBACK_OWNER)}


graph = StateGraph(TriageState)
graph.add_node("classify", classify)
graph.add_node("route", route)
graph.add_edge(START, "classify")
graph.add_edge("classify", "route")
graph.add_edge("route", END)

compiled = graph.compile()
runner: DaprWorkflowGraphRunner | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Build and start the runner at app startup, not at import time.

    The runner constructor contacts Catalyst (via DAPR_HTTP_ENDPOINT) to
    discover components, and start() opens the single outbound gRPC
    workflow stream (via DAPR_GRPC_ENDPOINT + DAPR_API_TOKEN). Doing this
    here keeps `import main` side-effect free and makes a bad endpoint fail
    loudly in the startup log instead of hanging the process.
    """
    global runner
    # Plain LangGraph above. This line makes each run a Catalyst durable workflow.
    runner = DaprWorkflowGraphRunner(graph=compiled, name="review-triage")
    runner.start()
    try:
        yield
    finally:
        runner.shutdown()


app = FastAPI(title="review-triage", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/triage/{place_id}")
def triage(place_id: str):
    # Plain def (not async): runner.invoke() blocks, so FastAPI runs this in a worker thread.
    try:
        reviews = list_reviews(place_id)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, e.response.text[:500])

    results = []
    for v in reviews:
        review_id = v.get("id")
        if PASS_REVIEW_BY == "text":
            workflow_input = {"place_id": place_id, "review_id": review_id,
                              "review": f"Rating {v.get('rating')}/5: {v.get('text', '')}"}
        else:  # reference: identifiers only cross into workflow state
            workflow_input = {"place_id": place_id, "review_id": review_id}

        # invoke() blocks until the durable workflow completes and returns final state.
        # For streaming progress use: async for ev in runner.run_async(...)
        assert runner is not None
        final = runner.invoke(workflow_input, thread_id=f"{place_id}:{review_id}")

        # Persist only the classification, never review text (Google/Yelp terms).
        results.append({
            "review_id": review_id,
            "classification": final.get("classification"),
            "owner": final.get("owner"),
        })
    return {"place": place_id, "mode": PASS_REVIEW_BY, "count": len(results), "results": results}
