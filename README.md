# dapr-catalyst-friction-less

A less-friction demo to catalyze your agents: a durable review-triage agent built with **LangGraph** and run on **Diagrid Catalyst 2.0**, packaged as one container that only makes outbound HTTPS calls.

Companion to the blog post [The Minimum-Approval Enterprise Agent](dapr-catalyst-8020-agent-blog.md). Read [FRICTIONS.md](FRICTIONS.md) before pitching this inside a large company.

## What it does

`POST /triage/{place_id}` fetches Google reviews for a place, and for each review runs a Catalyst durable workflow that (1) classifies the review with an LLM and (2) routes it to an owning team. If the container dies between step 1 and step 2, the workflow resumes at step 2 on restart; the LLM call is not repeated.

Use `place_id` = `sample` to run on the bundled `sample_reviews.json` with no Google key.

## Files

| File | Purpose |
|---|---|
| `main.py` | The whole agent: LangGraph graph, `DaprWorkflowGraphRunner`, FastAPI endpoint |
| `sample_reviews.json` | Five synthetic reviews so the demo runs without a Google key |
| `requirements.txt` | Pinned, verified installable together (Aug 16, 2026) |
| `Dockerfile` | `python:3.12-slim`, uvicorn on port 8080 |
| `.env.example` | Every environment variable the app reads |
| `dapr-catalyst-8020-agent-blog.md` | The blog post |
| `FRICTIONS.md` | Plain-language list of what will slow you down in an enterprise |
| `VERIFICATION-REPORT-2026-08-16.md` | Fact-check of every claim in the post, with sources |
| `CONTEXT-dapr-catalyst-blog-chat.md` | Decision log and open to-dos |

## Run it

1. Create a free Catalyst project at https://catalyst.diagrid.io and copy the three connection values (`DAPR_GRPC_ENDPOINT`, `DAPR_HTTP_ENDPOINT`, `DAPR_API_TOKEN`) from the console or `diagrid` CLI.
2. `cp .env.example .env` and fill it in. `GOOGLE_MAPS_API_KEY` is optional if you only use `sample`.
3. Local:
   ```bash
   python3.12 -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt
   set -a; . ./.env; set +a
   uvicorn main:app --port 8080
   curl -X POST localhost:8080/triage/sample
   ```
4. Container:
   ```bash
   docker build -t review-triage .
   docker run --rm -p 8080:8080 --env-file .env review-triage
   ```
5. Cloud Run / Azure Container Apps: commands are in the blog post's "Deploy" section.

## Things you will notice

- **The runner needs `DAPR_HTTP_ENDPOINT` as well as the gRPC endpoint.** On construction it calls the Dapr metadata API over HTTP to auto-discover components named `agent-memory`, `agent-pubsub`, `agent-registry` (all optional). Without a reachable HTTP endpoint the constructor blocks for `DAPR_HEALTH_TIMEOUT` seconds (default 60) retrying a health check. That is why `main.py` builds the runner in the FastAPI lifespan, not at import.
- **`runner.invoke()` is synchronous** and blocks until the durable workflow completes. `runner.run_async()` is an async generator that yields progress events if you want streaming.
- **"Six dependencies" is the direct list.** `pip freeze` after installing `requirements.txt` shows ~144 packages; `diagrid[langgraph]` pulls in `dapr-agents`, which pulls in the OpenAI, Anthropic, and Hugging Face client libraries whether you use them or not. Budget for that in your SBOM / vulnerability scan.
- **Python must be 3.11, 3.12, or 3.13.** `diagrid` declares `<3.14`.
- **License.** The `diagrid` package is Business Source License 1.1, not Apache-2.0. See FRICTIONS.md.

## License

Repository content: Apache-2.0 (see LICENSE). Third-party packages carry their own licenses; note the `diagrid` package's BSL 1.1 terms.
