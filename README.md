# dapr-catalyst-friction-less

**A durable AI agent that clears enterprise security review with one container and outbound port 443.** LangGraph on Diagrid Catalyst 2.0, run for real on the free tier, including a `kill -9` mid-workflow: Catalyst redelivered exactly one activity, the LLM step was never re-run, and the instance finished COMPLETED.

Start here: **[The Minimum-Approval Enterprise Agent](dapr-catalyst-8020-agent-blog.md)** (the blog post, ~15 min read). Then [RUNBOOK.md](RUNBOOK.md) to run it yourself, and [FRICTIONS.md](FRICTIONS.md) for the enterprise adoption playbook.

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
| `docs/` | Console screenshots referenced by the post, and the earlier long-form draft |
| `FRICTIONS.md` | Plain-language enterprise adoption playbook: what Catalyst takes off your plate, and how to answer the rest |
| `VERIFICATION-REPORT-2026-08-16.md` | Fact-check of every claim in the post, with sources |
| `CONTEXT-dapr-catalyst-blog-chat.md` | Decision log and open to-dos |
| `uvicornAppLog.md`, `clientLog.md`, `crashTestLog.md` | Verified first-run and crash-test logs from August 16, 2026 |

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
- **Review text stays out of Catalyst by default.** `PASS_REVIEW_BY=reference` (default) sends only `{place_id, review_id}` into the workflow; the classify activity fetches the text and uses it locally, so Catalyst's workflow history holds identifiers and classifications only. `PASS_REVIEW_BY=text` puts the text in state so you can see it in the console (sample data only).
- **Python 3.11 to 3.13** is supported.
- **License.** The `diagrid` package is Business Source License 1.1 (converts to Apache-2.0 in 2030); see FRICTIONS.md for how to fold that into the vendor conversation.

## License

Repository content: Apache-2.0 (see LICENSE). Third-party packages carry their own licenses; note the `diagrid` package's BSL 1.1 terms.
