# Crash test log - verified August 23, 2026

Terminal transcripts from a live crash test on the Catalyst free tier (`diagrid` 0.4.3,
`CRASH_TEST_DELAY=10` set in `.env` to widen the kill window). Procedure: RUNBOOK step 7.
An earlier run on August 16 produced the same result (console evidence:
`docs/catalyst-crash-instance.png`, instance `graph-sample:s1-11ea7c91`, 1.51m, COMPLETED).

## Terminal 1 - the crash

```text
(.venv) Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ uvicorn main:app --port 8080
INFO:     Started server process [12697]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
  [WORKFLOW] Step 0, pending_nodes=['classify']
  [ACTIVITY] Executing node 'classify' as Dapr activity
  [WORKFLOW] Step 1, pending_nodes=['route']
  [ACTIVITY] Executing node 'route' as Dapr activity
  [CRASH-TEST] route sleeping 10s: kill -9 the process now
Killed: 9
```

The classify activity (the LLM call) completed and its result was stored and signed by
Catalyst. The route activity was in flight when the process was hard-killed.

## Terminal 2 - the trigger and the kill

```text
Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ curl -s -X POST localhost:8080/triage/sample &
[1] 12759
Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ kill -9 $(pgrep -f "uvicorn main:app")
```

The backgrounded `curl` died with the process (dropped connection, no output). The work
did not: it was attached to Catalyst, not to the process.

## Terminal 1 - the restart, with no new request from anyone

```text
(.venv) Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ uvicorn main:app --port 8080
INFO:     Started server process [12771]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
  [ACTIVITY] Executing node 'route' as Dapr activity      <- Catalyst redelivers only the in-flight activity
  [CRASH-TEST] route sleeping 10s: kill -9 the process now   <- CRASH_TEST_DELAY still set; redelivered activity runs as written
  [WORKFLOW] Step 2, pending_nodes=['__end__']            <- workflow completes
```

## What this proves

- No `classify` line after the restart: the LLM result was already stored, so it was never
  re-run and never re-billed.
- The worker reconnected over the same outbound gRPC stream and Catalyst redelivered
  exactly one activity: the one that was in flight when the process died.
- The redelivered activity runs exactly as written, sleep included, which is why the
  `[CRASH-TEST]` line appears again on the restart.
- Console: instance `graph-sample:s1-a7fdd4d5`, status COMPLETED, execution time 38.16s
  (the crash plus the restart), among 34 total executions with zero failures. See
  `docs/catalyst-crash-resume.png`.

Note on the startup `UserWarning` (omitted above for brevity): the Dapr SDK prefers the
`grpc-<id>.cloud.r1.diagrid.io:443?tls=true` endpoint form; see RUNBOOK troubleshooting.
