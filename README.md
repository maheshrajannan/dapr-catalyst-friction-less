# dapr-catalyst-friction-less

A less-friction demo to catalyze your agents: a durable review-triage agent built with **LangGraph** and run on **Diagrid Catalyst 2.0**, packaged as one container that only makes outbound HTTPS calls.

Companion to the blog post [The Minimum-Approval Enterprise Agent](dapr-catalyst-8020-agent-blog.md). Read [FRICTIONS.md](FRICTIONS.md) for the enterprise adoption playbook: what Catalyst removes, and how to line up the rest.

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
| `RUNBOOK.md` | Step-by-step local run guide with prerequisites (Python 3.11+) and troubleshooting |
| `dapr-catalyst-8020-agent-blog.md` | The blog post |
| `FRICTIONS.md` | Plain-language enterprise adoption playbook: what Catalyst takes off your plate, and how to answer the rest |
| `VERIFICATION-REPORT-2026-08-16.md` | Fact-check of every claim in the post, with sources |
| `CONTEXT-dapr-catalyst-blog-chat.md` | Decision log and open to-dos |
| `uvicornAppLog.md`, `clientLog.md` | Verified first-run logs (server and client) from August 16, 2026 |

## Run it

Full step-by-step with troubleshooting: [RUNBOOK.md](RUNBOOK.md). Requires **Python 3.11 to 3.13**.

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

## Good to know

- **Set both `DAPR_HTTP_ENDPOINT` and `DAPR_GRPC_ENDPOINT`.** The runner uses HTTP on construction to auto-discover optional Catalyst components (`agent-memory`, `agent-pubsub`, `agent-registry`) and gRPC for the workflow stream. `main.py` builds the runner in the FastAPI lifespan so startup logs show connectivity clearly.
- **`runner.invoke()` is synchronous** and returns when the durable workflow completes. `runner.run_async()` is an async generator that yields progress events when you want streaming.
- **You get the whole agent toolkit.** `diagrid[langgraph]` brings the broader `dapr-agents` stack (about 144 packages, including the major LLM clients), so the other framework wrappers are already installed when you want them; run your SBOM scan once during the POC.
- **Python 3.11 to 3.13** is supported.
- **License.** The `diagrid` package is Business Source License 1.1 (converts to Apache-2.0 in 2030); see FRICTIONS.md for how to fold that into the vendor conversation.

## License

Repository content: Apache-2.0 (see LICENSE). Third-party packages carry their own licenses; note the `diagrid` package's BSL 1.1 terms.
