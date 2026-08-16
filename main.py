"""
Durable review-triage agent: LangGraph on Diagrid Catalyst.

One container, outbound-only networking. Fetches Google Places reviews,
classifies each with an LLM, routes it to an owning team, and runs each
review as a Catalyst durable workflow so a crash mid-run resumes at the
exact failed step instead of re-billing the LLM call.

Verified against diagrid==0.4.3 (Aug 2026). See README.md for setup.
"""
import json
import os
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


class TriageState(TypedDict, total=False):
    review: str
    classification: dict
    owner: str


llm = ChatAnthropic(model=os.environ.get("LLM_MODEL", "claude-sonnet-4-6"), temperature=0)


def classify(state: TriageState) -> TriageState:
    """Step 1 (durable activity): LLM classifies the review."""
    prompt = (
        "Classify this customer review. Return ONLY strict JSON with keys: "
        "sentiment (positive|neutral|negative), "
        "theme (service|product|cleanliness|pricing|other), "
        "urgency (act-now|monitor|none), "
        "summary (one sentence).\n\nReview:\n" + state["review"]
    )
    msg = llm.invoke(prompt)
    text = msg.text.strip()
    # tolerate ```json fences
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):text.rfind("}") + 1]
    return {"classification": json.loads(text)}


def route(state: TriageState) -> TriageState:
    """Step 2 (durable activity): map theme to owning team."""
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


async def fetch_reviews(place_id: str) -> list[dict]:
    """Return a list of {"id", "rating", "text"} for the place.

    place_id == "sample" loads bundled synthetic reviews so the demo runs
    with no Google key at all. Anything else calls Places API (New).
    """
    if place_id == "sample":
        return json.loads(SAMPLE_FILE.read_text())

    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise HTTPException(500, "GOOGLE_MAPS_API_KEY not set (or use place_id 'sample')")
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"{PLACES}/{place_id}",
            headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "reviews"},
        )
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text[:500])
    out = []
    for v in r.json().get("reviews", []):
        out.append({
            "id": v.get("name", ""),
            "rating": v.get("rating"),
            "text": (v.get("text") or {}).get("text", ""),
        })
    return out


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/triage/{place_id}")
async def triage(place_id: str):
    reviews = await fetch_reviews(place_id)
    results = []
    for v in reviews:
        review_text = f"Rating {v.get('rating')}/5: {v.get('text', '')}"
        # invoke() blocks until the durable workflow completes and returns final state.
        # For streaming progress use: async for ev in runner.run_async(...)
        assert runner is not None
        final = runner.invoke(
            {"review": review_text},
            thread_id=f"{place_id}:{v.get('id')}",
        )
        # Persist only the classification, never review text (Google/Yelp terms).
        results.append({
            "review_id": v.get("id"),
            "classification": final.get("classification"),
            "owner": final.get("owner"),
        })
    return {"place": place_id, "count": len(results), "results": results}
