(.venv) Maheshs-MacBook-Pro-3:dapr-catalyst-friction-less maheshrajannan$ uvicorn main:app --port 8080
INFO:     Started server process [59005]
INFO:     Waiting for application startup.
/Users/maheshrajannan/git/dapr-catalyst-friction-less/.venv/lib/python3.11/site-packages/dapr/conf/helpers.py:43: UserWarning: http and https schemes are deprecated for grpc, use myhost?tls=false or myhost?tls=true instead
  warn(
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
  [WORKFLOW] Step 0, pending_nodes=['classify']
  [ACTIVITY] Executing node 'classify' as Dapr activity
  [WORKFLOW] Step 1, pending_nodes=['route']
  [ACTIVITY] Executing node 'route' as Dapr activity
  [WORKFLOW] Step 2, pending_nodes=['__end__']
  [WORKFLOW] Step 0, pending_nodes=['classify']
  [ACTIVITY] Executing node 'classify' as Dapr activity
  [WORKFLOW] Step 1, pending_nodes=['route']
  [ACTIVITY] Executing node 'route' as Dapr activity
  [WORKFLOW] Step 2, pending_nodes=['__end__']
  [WORKFLOW] Step 0, pending_nodes=['classify']
  [ACTIVITY] Executing node 'classify' as Dapr activity
  [WORKFLOW] Step 1, pending_nodes=['route']
  [ACTIVITY] Executing node 'route' as Dapr activity
  [WORKFLOW] Step 2, pending_nodes=['__end__']
  [WORKFLOW] Step 0, pending_nodes=['classify']
  [ACTIVITY] Executing node 'classify' as Dapr activity
  [WORKFLOW] Step 1, pending_nodes=['route']
  [ACTIVITY] Executing node 'route' as Dapr activity
  [WORKFLOW] Step 2, pending_nodes=['__end__']
  [WORKFLOW] Step 0, pending_nodes=['classify']
  [ACTIVITY] Executing node 'classify' as Dapr activity
  [WORKFLOW] Step 1, pending_nodes=['route']
  [ACTIVITY] Executing node 'route' as Dapr activity
  [WORKFLOW] Step 2, pending_nodes=['__end__']
INFO:     127.0.0.1:64786 - "POST /triage/sample HTTP/1.1" 200 OK

