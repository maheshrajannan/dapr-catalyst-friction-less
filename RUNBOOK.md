# Runbook: run the review-triage agent locally

Step-by-step from a fresh clone to a working durable workflow. Companion to `README.md` (overview) and the blog post (deploy commands).

## Requirements

| Item | Requirement | Why |
|---|---|---|
| Python | **3.11 minimum**, up to 3.13 (3.14 not yet supported) | The `diagrid` package declares `>=3.11,<3.14`. Check with `python3 --version`. |
| Diagrid Catalyst account | Free tier at https://catalyst.diagrid.io | Provides the durable workflow engine, state, and pub/sub. |
| Anthropic API key | Pay-as-you-go account at https://platform.claude.com, prepaid balance ($5 is plenty) | LLM for the classify step. A Claude.ai Pro/Max subscription does not include API access; the API is billed separately. |
| Google Maps API key | Optional | Only needed for real Google Places reviews. The bundled `sample` place ID runs with no Google key. |
| macOS | Xcode command-line tools (`xcode-select --install`) | One dependency (`msgpack-python`) builds from source. |

## 1. Get the Catalyst connection values

1. Sign in at https://catalyst.diagrid.io and open (or create) a project.
2. Create an app (Manage → Apps → Create App). Any lowercase-hyphen name works, e.g. `review-triage`.
3. Copy the three connection values from the app's connect / API token panel:
   - `DAPR_GRPC_ENDPOINT`: use the form `grpc-<id>.cloud.r1.diagrid.io:443?tls=true` (the console may show `https://grpc-...:443`; both work, the `?tls=true` form avoids an SDK deprecation warning)
   - `DAPR_HTTP_ENDPOINT`: `https://http-<id>.cloud.r1.diagrid.io` (note: a **different host** that starts with `http-`, not the gRPC one)
   - `DAPR_API_TOKEN` (starts with `diagrid://`)

Both endpoints are needed: the runner discovers components over HTTP and streams workflow work over gRPC. The most common first-run mistake is pasting the gRPC URL into `DAPR_HTTP_ENDPOINT`; the symptom is a health-check loop against `grpc-...:443/v1.0/healthz/outbound`.

## 2. Get the Anthropic API key

1. Sign in at https://platform.claude.com (email or Google). A personal organization is created automatically.
2. Add a card and load a small prepaid balance (Settings → Billing).
3. API Keys → Create Key. Copy it now; it starts with `sk-ant-` and is shown once.

## 3. Configure

```bash
cd ~/git/dapr-catalyst-friction-less
cp .env.example .env
```

Edit `.env` and fill in `DAPR_GRPC_ENDPOINT`, `DAPR_HTTP_ENDPOINT`, `DAPR_API_TOKEN`, and `ANTHROPIC_API_KEY`. Leave `GOOGLE_MAPS_API_KEY` blank for now. `.env` is git-ignored and never leaves your machine.

## 4. Install

```bash
python3 --version                      # must print 3.11.x, 3.12.x, or 3.13.x
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt        # ~2-3 minutes, ~144 packages
```

If `pip` fails building `msgpack-python` (error mentions `longintrepr.h`), run `pip install msgpack` and repeat the last command.

## 5. Run

Terminal 1:

```bash
source .venv/bin/activate
set -a; source .env; set +a
uvicorn main:app --port 8080
```

Expected: `INFO: Application startup complete.` If instead you see repeated `Health check on ... failed`, `DAPR_HTTP_ENDPOINT` is wrong or unreachable; the runner retries for up to 60 seconds before giving up.

Terminal 2:

```bash
curl -s -X POST localhost:8080/triage/sample | python3 -m json.tool
```

Expected: JSON with `count: 5` and, for each review, a `classification` (sentiment, theme, urgency, summary) and an `owner` email. A verified first-run example is in `clientLog.md`; the matching server log is `uvicornAppLog.md`.

In Terminal 1 you will see, per review, the runner mapping the graph onto Dapr:

```text
[WORKFLOW] Step 0, pending_nodes=['classify']
[ACTIVITY] Executing node 'classify' as Dapr activity
[WORKFLOW] Step 1, pending_nodes=['route']
[ACTIVITY] Executing node 'route' as Dapr activity
[WORKFLOW] Step 2, pending_nodes=['__end__']
```

`[WORKFLOW]` lines are the orchestrator (one per LangGraph super-step); `[ACTIVITY]` lines are the durable, checkpointed units (one per node). The blog post's "What the first run showed" section has the diagram.

## 6. See it in Catalyst

Open the Catalyst console → Monitor → Workflows. You should see five `review-triage` workflow instances, each with two completed activities (classify, route) and a signed step history. Worth a screenshot for the blog.

## 7. The crash test

This is the point of the demo.

1. In Terminal 2, start a triage: `curl -s -X POST localhost:8080/triage/sample &`
2. Immediately press Ctrl-C in Terminal 1 to kill the app mid-run.
3. Restart it: `uvicorn main:app --port 8080`
4. In the Catalyst console, the interrupted workflow shows as resumed rather than restarted; the LLM step that already completed is not re-run and not re-billed.

## 8. Real Google reviews (optional)

1. In a billed GCP project, enable **Places API (New)** and create an API key.
2. Add `GOOGLE_MAPS_API_KEY=...` to `.env` and reload it (`set -a; source .env; set +a`).
3. Find a place ID (e.g. from https://developers.google.com/maps/documentation/places/web-service/place-id) and call `curl -s -X POST localhost:8080/triage/<place_id>`.

Only the classification is stored, never the review text, per Google's terms.

## 9. Container

```bash
docker build -t review-triage .
docker run --rm -p 8080:8080 --env-file .env review-triage
```

## 10. Cloud

Cloud Run and Azure Container Apps commands are in the "Deploy" section of `dapr-catalyst-8020-agent-blog.md`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Health check on http://127.0.0.1:3500/... failed` on startup | `DAPR_HTTP_ENDPOINT` not set or not exported | `set -a; source .env; set +a` before `uvicorn` |
| `Health check on https://grpc-...:443/v1.0/healthz/outbound failed` | The gRPC URL was pasted into `DAPR_HTTP_ENDPOINT` | Use the `http-...` host for `DAPR_HTTP_ENDPOINT` |
| `[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate` (macOS) | python.org Python has no root certs wired in | Run `/Applications/Python 3.11/Install Certificates.command`, or add `SSL_CERT_FILE=$(python -m certifi)` and `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=$(python -m certifi)` to `.env` |
| `UserWarning: http and https schemes are deprecated for grpc` | Old endpoint form | Use `grpc-<id>.cloud.r1.diagrid.io:443?tls=true` |
| `TypeError: ... missing 1 required keyword-only argument: 'name'` | Older code without `name=` | Pull latest `main.py` |
| `ModuleNotFoundError: diagrid.workflow` | Wrong import path | Use `from diagrid.agent.langgraph import DaprWorkflowGraphRunner` |
| `401`/`403` from Catalyst | Wrong or expired `DAPR_API_TOKEN` | Regenerate the app token in the console |
| `authentication_error` from Anthropic | Wrong key or no balance | Check platform.claude.com → API Keys / Billing |
| `pip` fails on `msgpack-python` | Old package needs build tools | `pip install msgpack`, then retry; on macOS `xcode-select --install` |
| `python3 --version` shows 3.9 or 3.10 | Too old for `diagrid` | Install 3.11+ (`brew install python@3.12`) and create the venv with it |
