# Verification Report: dapr-catalyst-8020-agent-blog.md

Date: August 16, 2026. Method: every claim, reference, CLI flag, API path, and SDK call in the post was checked against primary sources (vendor docs, source repos, press releases, PyPI, terms-of-service pages). Four parallel review passes: launch/press claims, SDK/code, review APIs, deploy commands; plus a fifth pass on enterprise adoption friction. Verdicts: VERIFIED, WRONG (fixed), PARTLY WRONG (fixed), UNVERIFIABLE.

## Summary

| Area | Checked | Wrong / fixed | Notes |
|---|---|---|---|
| Catalyst 2.0 launch, press, Dapr 1.18 | 12 | 0 wrong, 5 precision fixes | Every source exists; a few names/baselines tightened |
| `diagrid` SDK and LangGraph code | 9 | 3 hard errors, 2 soft | Import path, `arun`, missing `name=` would fail on first run |
| Yelp / Google Places | 7 | 2 material | Yelp no free tier; 24-hour storage cap. Demo switched to Places |
| gcloud / az / Cloud Run / model ID | 7 | 1 hard, 2 outdated | `az containerapp up` secrets; VPC connector superseded; ACA internal ingress + scheduler |
| Enterprise adoption friction (new) | 12 areas | n/a | Added 4 new rows to the frictions table |

## 1. Catalyst 2.0 launch and press claims

| Claim in post | Verdict | Fix applied | Source |
|---|---|---|---|
| Diagrid blog "Agentic Durable Execution", July 27, 2026 | VERIFIED (title incomplete) | Full title added: "Agentic Durable Execution: Durable and Verifiable AI Agent Workflows", author Mark Fussell | https://www.diagrid.io/blog/what-is-agentic-durable-execution |
| Catalyst 2.0 launched July 28, 2026, Business Wire | VERIFIED | Full headline + URL added to references | https://www.businesswire.com/news/home/20260728284090/en/ |
| Durable execution (resume at failed step) + verifiable execution (signed history) | VERIFIED | none | SiliconANGLE, PR |
| Signing lineage from Dapr 1.18 | VERIFIED | Added date: Dapr 1.18.0 released June 10, 2026 | https://github.com/dapr/dapr/releases/tag/v1.18.0 |
| Multi-cloud, on-prem, air-gapped | VERIFIED | Reworded to the four documented topologies (Cloud, Dedicated, Self-Hosted, Air-Gapped) | https://docs.diagrid.io/operate/hosting/ |
| Framework list | VERIFIED with naming errors | "LangGraph Deep Agents" -> "LangChain Deep Agents"; Spring AI added (HolmesGPT also documented, omitted as niche) | https://docs.diagrid.io/develop/agents/ |
| "10x performance" | VERIFIED, baseline missing | Qualified: "up to 10x vs open-source Dapr", vendor-stated self-comparison | Business Wire PR |
| Pricing per concurrent workflow, no per-step metering | VERIFIED | none | https://www.diagrid.io/pricing |
| SiliconANGLE article | VERIFIED | Title/author/URL added: Duncan Riley, "Diagrid Catalyst 2.0 adds durable execution to more than 10 agent frameworks" | https://siliconangle.com/2026/07/28/diagrid-catalyst-2-0-adds-durable-execution-10-agent-frameworks/ |
| The New Stack article | VERIFIED | Author/URL added: Frederic Lardinois | https://thenewstack.io/diagrid-catalyst-agent-recovery/ |
| "outbound gRPC/HTTPS with API token" | VERIFIED, both protocols | Text now says HTTP or gRPC; `DAPR_HTTP_ENDPOINT` added alongside `DAPR_GRPC_ENDPOINT`; API list expanded (service invocation, bindings) | https://docs.diagrid.io/operate/hosting/connect/ |
| Built on OSS Dapr Workflows; self-host is exit path | VERIFIED with caveats | Caveat added: Catalyst lacks Actors, Secrets, Configuration, Distributed Lock APIs | https://docs.diagrid.io/catalyst/dapr-compatibility/ |

## 2. `diagrid` SDK and LangGraph code

| Claim in post | Verdict | Fix applied | Source |
|---|---|---|---|
| PyPI package `diagrid` | VERIFIED | Version pinned in prose: 0.4.3, Aug 4, 2026; install extra `diagrid[langgraph]` | https://pypi.org/project/diagrid/ |
| `from diagrid.workflow import DaprWorkflowGraphRunner` | **WRONG** (module does not exist; ImportError) | `from diagrid.agent.langgraph import DaprWorkflowGraphRunner` | https://raw.githubusercontent.com/diagridio/python-ai/main/diagrid/agent/langgraph/runner.py |
| `DaprWorkflowGraphRunner(g.compile())` | **WRONG** (`name=` is required kwarg; TypeError) | `DaprWorkflowGraphRunner(graph=g.compile(), name="review-triage")` | same |
| `await runner.arun({...})` | **WRONG** (no such method; AttributeError) | `runner.invoke(input, thread_id=...)` (sync) — `run_async()` is an async generator, noted in comment | same; examples/langgraph/simple_graph.py |
| Runner lifecycle | Missing | Added `runner.start()` / `runner.shutdown()` via FastAPI lifespan | examples/langgraph/simple_graph.py |
| docs.diagrid.io/develop/agents/langgraph | VERIFIED | Trailing slash; noted sub-page for durable-workflow tutorial | https://docs.diagrid.io/develop/agents/langgraph/ |
| `diagrid-labs/dapr-agents-catalyst-samples` | VERIFIED exists, wrong for LangGraph | Repointed source of truth to `diagridio/python-ai` `examples/langgraph/` | https://github.com/diagridio/python-ai |
| `DAPR_GRPC_ENDPOINT`, `DAPR_API_TOKEN` | VERIFIED | Added `DAPR_HTTP_ENDPOINT` | https://docs.diagrid.io/operate/hosting/connect/ |
| LangGraph checkpointers "need self-hosted Postgres or Redis" | PARTLY WRONG | Reworded: Postgres you run, SQLite (dev only), Cosmos DB, or LangGraph Platform hosted persistence (another SaaS vendor). "super-step boundary" terminology confirmed correct | https://docs.langchain.com/oss/python/langgraph/checkpointers |
| `set_entry_point` | VERIFIED, not idiomatic | Switched to `add_edge(START, ...)` | https://reference.langchain.com/python/langgraph/graph/state/StateGraph |
| `msg.content` on `ChatAnthropic` | VERIFIED, fragile | Switched to `msg.text` (content can be a list of blocks) | https://docs.langchain.com/oss/python/integrations/chat/anthropic |
| `claude-sonnet-4-6` model ID | VERIFIED | Left as-is. Anthropic uses dateless IDs from 4.6 onward; `claude-sonnet-5` is newest | https://platform.claude.com/docs/en/about-claude/models/overview |

## 3. Review APIs

| Claim in post | Verdict | Fix applied | Source |
|---|---|---|---|
| Yelp returns up to 3 excerpts | PARTLY WRONG (plan-dependent: Base 0, Enhanced 3, Premium 7; excerpts are 160 chars) | Moved to caveats with plan detail | https://docs.developer.yelp.com/reference/v3_business_reviews ; https://business.yelp.com/data/resources/pricing/ |
| Yelp endpoint/auth/response shape | VERIFIED | n/a (code no longer uses Yelp) | same |
| Yelp API key freely available | **WRONG** — 30-day/5,000-call trial then $229/mo Base (no review text), $299/mo Enhanced | **Demo switched to Google Places API (New)** per your decision | https://business.yelp.com/data/resources/pricing/ |
| Yelp restricts long-term storage | VERIFIED, stricter than stated: 24-hour cap (API Terms §5(a)) | Stated as 24 hours | https://terms.yelp.com/developers/api_terms/20250113_en_us/ |
| Google Places up to 5 reviews | VERIFIED (both legacy and New) | Now the primary path; code uses `GET places.googleapis.com/v1/places/{id}` with `X-Goog-Api-Key` and `X-Goog-FieldMask: reviews`; `text` is a `LocalizedText` object | https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places |
| Requires billed GCP project | VERIFIED; free-tier detail updated | $200 credit replaced March 2025 by per-SKU free calls; reviews are Enterprise + Atmosphere SKU | https://mapsplatform.google.com/pricing/ |
| Google terms on caching reviews | VERIFIED (ToS §3.2.3 no scraping/caching; only lat/lng 30 days and place_id cacheable) | Stated in caveats and code comment | https://cloud.google.com/maps-platform/terms/ |

## 4. Deploy commands and platform claims

| Claim in post | Verdict | Fix applied | Source |
|---|---|---|---|
| `gcloud run deploy` flags incl. `--set-secrets` multi-secret syntax | VERIFIED | Env/secret names updated for Places | https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy |
| `gcloud scheduler jobs create http` flags | VERIFIED; `--location` needed in practice | `--location us-central1` added | https://docs.cloud.google.com/sdk/gcloud/reference/scheduler/jobs/create/http |
| `az containerapp up ... --env-vars KEY=secretref:name` | **WRONG** — `up` has no `--secrets`; command errors on missing secret | Split into `up` -> `secret set` -> `update --set-env-vars` | https://github.com/microsoft/azure-container-apps/issues/340 |
| ACA `--ingress internal` + external scheduler | CAVEAT — internal FQDN unreachable from internet | Switched to `--ingress external` with auth note; suggested Container Apps job as internal trigger | https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview |
| Cloud Run: VPC-SC, CMEK, internal ingress, IAM, GPUs | VERIFIED (all five) | Added: Cloud Run internal ingress explicitly admits Cloud Scheduler | https://docs.cloud.google.com/run/docs/securing/ingress |
| Serverless VPC connector | SUPERSEDED — Direct VPC egress is the recommended default | Reworded; connector kept as Cloud NAT option | https://docs.cloud.google.com/run/docs/configuring/connecting-vpc |

## 5. Enterprise adoption friction (added to the post)

New rows in "Remaining frictions" based on this pass:

| Finding | Verdict | Source |
|---|---|---|
| `diagrid` SDK license is **Business Source License 1.1**, not open source. Production use requires a commercial license unless <60 FTE and <$15M revenue; converts to Apache-2.0 on March 1, 2030. PyPI metadata does not show it. Whether a Catalyst subscription includes it is not stated. | CONFIRMED | https://raw.githubusercontent.com/diagridio/python-ai/main/LICENSE.md |
| Compliance: SOC 2 Type II (Aug 2024). No public ISO 27001, HIPAA, FedRAMP; no public trust center or subprocessor list; ToS allows aggregated/de-identified usage data for any lawful purpose. | CONFIRMED / UNVERIFIABLE (others) | https://www.diagrid.io/blog/diagrid-achieves-soc-2-type-ii-compliance ; https://www.diagrid.io/terms-of-service |
| Shared Catalyst Cloud: one public data-plane region (aws-us-west-1), public internet. Azure Private Link for Dedicated regions shipped Aug 10, 2026; no AWS PrivateLink / GCP PSC evidence. | CONFIRMED | https://status.diagrid.io/ ; https://docs.diagrid.io/catalyst/release-notes/ |
| Self-hosted requires dedicated Kubernetes 1.24+, external Postgres (`wal_level=logical`), Helm agent with cluster-scoped RBAC, outbound to six `*.r1.diagrid.io` endpoints not TLS-inspected; air-gapped install docs not public. | CONFIRMED | https://docs.diagrid.io/operate/hosting/enterprise-self-hosted/production-planning/ |
| App auth = static `DAPR_API_TOKEN` bearer per app; no documented rotation/OIDC federation for external apps; console SSO federation API July–Aug 2026; no SCIM. | CONFIRMED | https://docs.diagrid.io/operate/platform-operations/identity-and-access/ |
| Workflow history stores every step's inputs/outputs; visible in console; encryption-at-rest / CMK not documented. | CONFIRMED / UNVERIFIABLE | https://docs.diagrid.io/concepts/workflows/ |
| Vendor: founded 2021, Series A $24.2M (2022), no later round found; SDK repo 6 stars, 3 contributors, first PyPI release March 2026. | CONFIRMED | https://www.cbinsights.com/company/diagrid ; https://github.com/diagridio/python-ai |
| Outbound-only holds for workflows and publish (app-initiated gRPC stream); subscribe/bindings/invocation require inbound from Catalyst egress IP. | CONFIRMED | https://docs.diagrid.io/develop/connect/ |
| gRPC honors HTTPS_PROXY/NO_PROXY; Dapr Python SDK sets no keepalive (open issue #813); Diagrid has no proxy guidance. | CONFIRMED | https://github.com/dapr/python-sdk/issues/813 |
| Free tier: 3 projects, 10 apps, 3 users, 512 MB/store, 100 req/s/app, 100k req/day/project, no SLA. | CONFIRMED | https://docs.diagrid.io/operate/plans-and-support/ |

## Could not verify

- Prose of `docs.diagrid.io/develop/agents/langgraph/langgraph-durable-workflow/` (JS-rendered). Code was verified against repo source and examples instead.
- Whether Diagrid holds ISO 27001 / HIPAA / FedRAMP (no public claim found; treated as not held).
- Encryption at rest and CMK for Catalyst's managed workflow store.
- Whether Catalyst subscription bundles the BSL SDK commercial license.
- AWS PrivateLink / GCP PSC availability for Dedicated regions.
- Yelp's exact effective date for current pricing tiers.
