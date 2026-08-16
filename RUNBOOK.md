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

Expected: JSON with `mode: "reference"`, `count: 5` and, for each review, a `classification` (sentiment, theme, urgency, summary) and an `owner` email. A verified first-run example is in `clientLog.md`; the matching server log is `uvicornAppLog.md`.

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

Open the Catalyst console → Monitor → Workflows. The graph is listed as **`dapr.langgraph.ReviewTriage.workflow`** (the runner derives this from `name="review-triage"`), attributed to your app, with a **Total executions** count (5 per triage call) and a status bar that should be fully green. Click the row or "All workflow executions" to open individual instances; each shows the two activities (classify, route) and the signed step history. Verified August 16, 2026: 10 executions after two calls, all succeeded (screenshot: `docs/catalyst-workflows-console.png`).

## 7. The crash test

This is the point of the demo, so it is worth doing properly. Two things matter:

- **Ctrl-C is not a crash.** It asks uvicorn to shut down gracefully: in-flight requests finish, then `runner.shutdown()` drains the worker. The current review completes and Catalyst never sees a failure. (You may also see a `KeyboardInterrupt` / `CancelledError` traceback after `Finished server process`; that is uvicorn shutdown noise, not an error in the app.) Use `kill -9`, which is what a real crash, OOM-kill, or node eviction looks like.
- **The window is tiny by default.** Classify takes a few seconds (LLM call); route takes milliseconds. `CRASH_TEST_DELAY` makes route sleep so you can hit the gap between the two checkpoints.

Steps:

```bash
# Terminal 1: start with a 20-second window in the route step
source .venv/bin/activate
set -a; source .env; set +a
CRASH_TEST_DELAY=20 uvicorn main:app --port 8080

# Terminal 2: fire one triage (it will not return; that is expected)
curl -s -X POST localhost:8080/triage/sample &

# Terminal 1 shows: [ACTIVITY] Executing node 'classify' ... then
#                   [CRASH-TEST] route sleeping 20s: kill -9 the process now
# Terminal 2: kill it hard within those 20 seconds
kill -9 $(pgrep -f "uvicorn main:app")

# Terminal 1: restart WITHOUT the delay
uvicorn main:app --port 8080
```

What you will see after the restart, in Terminal 1, with no new request from anyone (verified August 16, 2026):

```text
INFO:     Application startup complete.
  [ACTIVITY] Executing node 'route' as Dapr activity   <- Catalyst redelivers only the in-flight activity
  [WORKFLOW] Step 2, pending_nodes=['__end__']         <- workflow completes
```

Two lines. No `classify` activity (its result was already stored; no second LLM call, no second charge) and no visible replay of steps 0 and 1 (the orchestrator finishes from history). In the Catalyst console the same instance shows as completed with both activities, not as a new instance. The full before/after log is in `crashTestLog.md`.

What to capture in the Catalyst console (two screenshots):

1. **Workflows list** (Monitor → Workflows): `dapr.langgraph.ReviewTriage.workflow` now shows one more execution than before the test (11 if you had 10) and the status bar is still fully green. Point: the crashed run counted as a completion, not a failure plus a retry. Save as `docs/catalyst-crash-resume.png`.
2. **The instance detail** (click the row → All workflow executions → the newest instance, e.g. `graph-sample:s1-<suffix>`): Status COMPLETED; **Execution time** of a minute or more (siblings take seconds), which is the crash gap; and in Event history one `execute_node_activity` scheduled/completed for classify, then route scheduled, a gap, route completed, execution completed. Scroll the history so the whole sequence is in frame. This is the strongest single piece of evidence in the whole demo. Save as `docs/catalyst-crash-instance.png`. Verified August 16, 2026: instance `graph-sample:s1-11ea7c91`, 11:35:51 to 11:37:21, 1.51m, COMPLETED.

Also open the instance's **Output** panel. In the default `PASS_REVIEW_BY=reference` mode, `output` and `channel_state.values` contain only `place_id`, `review_id`, the classification, and the owner: no review text enters Catalyst's workflow history, because the classify activity fetches the text itself and uses it locally. (The **Input** panel's `graph_config.channels_read` will still list `review` by name; that is the declared state schema, not a value.) Verified August 16, 2026 on instance `graph-sample:s5-ca2e2248`; save as `docs/catalyst-reference-mode.png`. Set `PASS_REVIEW_BY=text` to see the full state including review text in the console instead; useful for demos with the bundled sample data, and exactly what you would not do with real third-party reviews.

What just happened, as a sequence:

```mermaid
sequenceDiagram
    autonumber
    participant T2 as Terminal 2 (curl)
    participant P1 as uvicorn #1 (CRASH_TEST_DELAY=10)
    participant CAT as Catalyst workflow engine
    participant LLM as LLM
    participant P2 as uvicorn #2 (restart, no delay)
    T2->>P1: POST /triage/sample
    P1->>CAT: start workflow (review s1)
    CAT->>P1: run activity: classify
    P1->>LLM: classify prompt
    LLM-->>P1: classification JSON
    P1-->>CAT: classify result stored + signed
    CAT->>P1: run activity: route
    Note over P1: route sleeps 10s
    T2-->>P1: kill -9
    Note over P1,T2: process gone; curl gets a dropped connection
    P2->>CAT: worker reconnects (outbound gRPC, same app)
    CAT->>P2: redeliver activity: route (classify NOT redelivered)
    P2-->>CAT: route result stored + signed
    CAT-->>P2: workflow complete (Step 2, __end__)
    Note over CAT: console: same instance, both activities done, no failure
```

Note the `curl` in Terminal 2 will report a dropped connection; the HTTP caller was collateral of the crash, but the work was not. The completed classification lives in Catalyst either way, which is the durability argument in one sentence.

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
