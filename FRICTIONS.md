# From "frictionless" to "friction-less": what Catalyst removes, and how to line up the rest

*Written August 16, 2026. Every point below was checked against Diagrid's docs, source code, or public records; links follow each section. Written so anyone, not just a cloud architect, can follow it.*

## The one-paragraph answer

Diagrid Catalyst lets your AI agent be a single program that only ever *calls out* to the internet. You never ask your company's network team to open a door inward, and you never file tickets for databases, message queues, or a Kubernetes cluster just to get one agent into production. That is a big deal: in most large companies those tickets are where agent projects stall. What Catalyst does is *consolidate* the remaining work into one conversation, the vendor onboarding, and it gives you good answers to bring to it. Below are the ten things that conversation will cover, what Catalyst already offers for each, and what to ask for.

## What Catalyst takes off your plate

- **Durability without writing retry code.** If the agent crashes after an expensive LLM call, it resumes at the next step. Nothing is re-billed, nothing is duplicated.
- **A signed audit trail for free.** Every step is cryptographically signed (this came from open-source Dapr 1.18). "What did the agent do?" has an answer.
- **State, pub/sub, and workflows as a service.** No Redis, no Kafka, no cluster inside your perimeter for the app.
- **A one-sentence security review.** "Outbound HTTPS on port 443 to three allowlisted domains." Three firewall rows.
- **Framework freedom.** Works underneath LangGraph, LangChain Deep Agents, Google ADK, Microsoft Agent Framework, OpenAI Agents SDK, AWS Strands, CrewAI, PydanticAI, Claude Agent SDK, Spring AI, and Dapr Agents. Keep the framework you already have.
- **A real exit path.** Built on open-source CNCF Dapr Workflows; the same application code runs on Dapr you host yourself.

## The ten things to line up, and how Catalyst answers each

### 1. SDK licensing: know the model, and it is a clean one

**What it is:** Open-source Dapr is Apache-2.0. The `diagrid` Python package (the wrapper that makes LangGraph durable) uses the **Business Source License 1.1**: free in production for small organizations, a commercial license for larger ones, and it converts to Apache-2.0 on **March 1, 2030**. This is a well-established model used by other infrastructure companies to fund open-source work.

**How to handle it:** Bundle the license confirmation into the same vendor package as the security review. Ask Diagrid to confirm in writing that a Catalyst subscription includes the SDK license. One conversation, not two.

Source: https://raw.githubusercontent.com/diagridio/python-ai/main/LICENSE.md

### 2. Compliance: SOC 2 Type II in hand, more on the way

**What it is:** Diagrid attained **SOC 2 Type II** in August 2024 with continuous monitoring, and its terms include a Data Processing Agreement by default. Additional certifications (ISO 27001, FedRAMP) are not yet publicly listed.

**How to handle it:** Request the SOC 2 report and subprocessor list under NDA on day one of the POC so paperwork runs in parallel with the build. Where a specific certification is a gate, ask for the roadmap; the company's CNCF pedigree and enterprise references (HSBC, Prudential, FICO, Zeiss, Uniphar) help that conversation.

Sources: https://www.diagrid.io/blog/diagrid-achieves-soc-2-type-ii-compliance ; https://www.diagrid.io/terms-of-service

### 3. Data placement: a hosting tier for every data class

**What it is:** To resume after a crash and to produce the signed audit trail, Catalyst stores each step's inputs and outputs. That is the feature working as designed. The shared free tier runs in AWS us-west-1.

**How to handle it:** Design the workflow to carry identifiers and short summaries rather than full content (this demo stores only the classification, never the review text). Then pick the tier that fits the data: **Cloud** for POC, **Dedicated** or **BYOC** when you need private networking and residency, **Self-Hosted** or **Air-Gapped** for sovereign data. Same code across all four.

Sources: https://docs.diagrid.io/concepts/workflows/ ; https://docs.diagrid.io/operate/hosting/ ; https://www.diagrid.io/pricing

### 4. Private networking: shipping now, moving fast

**What it is:** Azure Private Link for Catalyst dedicated regions shipped on **August 10, 2026**, and dedicated regions can be placed inside your own subscription. The release notes show three control-plane releases in the first two weeks of August.

**How to handle it:** Start the POC on the shared cloud; ask about AWS PrivateLink and GCP Private Service Connect timing during it. At this cadence, the answer may arrive before your production date.

Source: https://docs.diagrid.io/catalyst/release-notes/

### 5. Self-hosting: same code, and the platform team owns the platform

**What it is:** If policy says "self-host," Catalyst installs by Helm onto a Kubernetes cluster your platform team already runs, backed by an external PostgreSQL. Your agent team never touches it; the application code is unchanged.

**How to handle it:** Prove value first with the outbound-only POC, then bring the platform team a self-hosting plan for scale-out. That ordering turns "we would need a cluster" from a blocker into a year-two upgrade.

Source: https://docs.diagrid.io/operate/hosting/enterprise-self-hosted/production-planning/

### 6. Identity: rotate today, federate tomorrow

**What it is:** Your app authenticates with a per-app API token over TLS. Diagrid's internal stack already uses SPIFFE workload identity and mTLS; console identity-provider federation shipped in July 2026 and per-region OIDC discovery in August.

**How to handle it:** Store the token in your cloud secret manager and rotate on your existing schedule. Ask about workload-identity federation for external apps during the POC; the pieces are clearly in flight.

Source: https://docs.diagrid.io/operate/platform-operations/identity-and-access/

### 7. Company and community: founders of Dapr, CNCF maintainers, fast cadence

**What it is:** Diagrid was founded in 2021 by the creators of Dapr, is a CNCF maintainer, and raised a $24.2M Series A led by Norwest. The `diagrid` SDK first shipped in March 2026 and is on 0.4.3, with a rapid release rhythm; the framework list grew to eleven in a single release.

**How to handle it:** Pin versions and follow the `diagridio/python-ai` examples as source of truth. Because Catalyst is built on open-source Dapr, business continuity has a real answer: self-host Dapr with the same application code.

Sources: https://www.cbinsights.com/company/diagrid ; https://github.com/diagridio/python-ai ; https://pypi.org/project/diagrid/#history

### 8. Corporate proxies: standard variables, one thing to test

**What it is:** Your app keeps a single long-running outbound connection to Catalyst to receive work. gRPC honors the standard `HTTPS_PROXY` / `NO_PROXY` variables, so no architecture change is needed.

**How to handle it:** Test that connection against your real proxy in week one, and enable gRPC keepalives if the proxy is aggressive about idle connections (see the linked issue for the option). Ten minutes of testing early saves a mystery later.

Source: https://github.com/dapr/python-sdk/issues/813

### 9. Dependency footprint: you get the whole agent toolkit

**What it is:** The app lists six packages. `diagrid[langgraph]` brings the broader `dapr-agents` toolkit along (about 144 packages in a fresh install, including the major LLM client libraries), which means the other framework wrappers are already there when you want them.

**How to handle it:** Your SBOM and vulnerability scan will see the full stack; run it once during the POC. Python 3.11 through 3.13 is supported.

Source: `pip freeze` after installing `requirements.txt` in this repo.

### 10. Outbound-only: a clear line, easy to stay on

**What it is:** Running workflows and *publishing* events are fully outbound; your app opens the connection and pulls work. If you later *subscribe* to topics, add input bindings, or use service invocation, Catalyst reaches your app, and you allowlist its egress IP inbound. Both modes are documented.

**How to handle it:** This demo publishes and never subscribes, so it stays outbound-only. When a future feature needs the inbound path, you will know exactly what to ask the network team for.

Source: https://docs.diagrid.io/develop/connect/

## Smaller things worth knowing

- **Free-tier limits:** 3 projects, 10 apps, 3 users, 512 MB per store, 100 requests per second per app, 100k requests per day per project. Plenty for a proof of concept.
- **API surface:** Catalyst offers state, pub/sub, service invocation, bindings, and workflows, which is exactly what this design uses, so "same code on self-hosted Dapr" holds for it.
- **The "up to 10x" performance figure** is Catalyst relative to open-source Dapr, per Diagrid.
- **Replay is a new mental model:** durable workflows replay your orchestration code on resume and return stored results for finished steps. One team session on this before the first incident, and it becomes the reason your on-call is quiet.
- **Google Places, the demo's input:** up to 5 reviews per place, needs a billed GCP project, and its terms forbid storing review text (the demo stores only the classification). Yelp Fusion is now a paid product, which is why the demo uses Places.

## The honest pitch, said positively

Use Catalyst's free tier to get a durable, auditable agent running in a sandbox in an afternoon, with a security story that fits in one sentence. Use that working demo to earn the vendor conversation, and walk into it with the ten points above already answered. Whatever the outcome, the same LangGraph code runs on open-source Dapr Workflows, so the work is never stranded. That is a stronger position than almost any other agent-infrastructure choice offers today.
