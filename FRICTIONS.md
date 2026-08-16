# Is Diagrid Catalyst really "frictionless"? The plain-English list

*Written August 16, 2026. Every point below was checked against Diagrid's own docs, source code, or public records; links are at the bottom of each section. Written so anyone, not just a cloud architect, can follow it.*

## The one-paragraph answer

Catalyst lets your app be a single program that only ever *calls out* to the internet, so you never ask your company's network team to open a door inward or to set up databases and message queues for you. That part is true, and it removes a real pile of paperwork. What it does **not** remove is the paperwork of bringing a *new vendor* into a big company: legal review, security review, licensing, and "what happens if they go out of business." It also assumes you are OK with your agent's step-by-step data living on someone else's servers. So: it trades many small internal tickets for one big external one. Whether that is a good trade depends on how strict your company is. For a Fortune-100 like Caterpillar, several of these will bite.

## The frictions, biggest first

### 1. The Python library is not open source, even though "Dapr" is

**What it means:** Dapr (the open-source project) is free to use, forever, under the Apache-2.0 license. But the `diagrid` Python package, the thing you `pip install` to make LangGraph durable, is under a different license called **Business Source License 1.1**. That license says: if your company has more than 60 employees or more than $15 million in revenue, you need a paid commercial license from Diagrid to run it in production. It only becomes truly open source on **March 1, 2030**.

**Why it matters:** Any big company has an open-source review board. This will be the first thing they flag. Also, PyPI (where you download it) does not even display the license, so it is easy to miss.

**What to ask Diagrid:** "Does a Catalyst subscription include the commercial license for the `diagrid` SDK? Put it in writing."

Source: https://raw.githubusercontent.com/diagridio/python-ai/main/LICENSE.md

### 2. Their compliance paperwork is thin

**What it means:** Big companies ask vendors for certificates that prove they handle data safely. Diagrid has **SOC 2 Type II** (a good baseline, since August 2024). They do **not** publicly claim ISO 27001, HIPAA, or FedRAMP. There is no public "trust center" web page and no public list of *their* sub-vendors (subprocessors). Their terms of service also let them use aggregated, anonymized usage data however they like.

**Why it matters:** If your security team's checklist says "must have ISO 27001," this is a no today. Even if not, expect a longer questionnaire round.

Sources: https://www.diagrid.io/blog/diagrid-achieves-soc-2-type-ii-compliance ; https://www.diagrid.io/terms-of-service

### 3. Your agent's data goes to their cloud, and only one region is public

**What it means:** Every step your agent takes (the prompt sent to the LLM, the review text, the tool inputs and outputs) is saved in Catalyst's workflow history so it can resume after a crash. That history is stored on Diagrid's servers and is visible in their web console. The shared (free) service runs in **one region: AWS us-west-1**, over the public internet. Encryption at rest and "bring your own key" are not documented.

**Why it matters:** If the data is customer PII, or if your policy says "EU data stays in the EU," the free tier is out. You would need their Dedicated or Bring-Your-Own-Cloud plans (starting around $1,199 to $1,599 per month) or self-hosting.

**How to soften it:** Pass IDs and short summaries through the workflow, not full content. The demo already stores only the classification, never the review text.

Sources: https://docs.diagrid.io/concepts/workflows/ ; https://status.diagrid.io/ ; https://www.diagrid.io/pricing

### 4. Private networking is brand new

**What it means:** Big companies prefer traffic to a vendor to go over a private link instead of the open internet. Azure Private Link for Catalyst dedicated regions shipped on **August 10, 2026** (days ago). There is no public evidence yet of AWS PrivateLink or Google Private Service Connect.

**Why it matters:** If "no vendor traffic over the public internet" is a rule, you are on Azure or you wait.

Source: https://docs.diagrid.io/catalyst/release-notes/

### 5. "No Kubernetes cluster" is true for your app, not for the escape hatch

**What it means:** The pitch is that you do not need to run a cluster. True, *your app* does not. But if compliance says "you must self-host," then self-hosted Catalyst needs a **dedicated Kubernetes cluster**, an external **PostgreSQL** database configured a specific way, a Helm-installed agent with broad cluster permissions, and outbound access to six `*.r1.diagrid.io` addresses that must **not** be inspected by your corporate proxy. The fully air-gapped install guide is not public.

**Why it matters:** The self-hosted fallback is exactly the kind of platform-team project the whole approach was supposed to avoid. Treat it as a year-two option, not the answer to a proof-of-concept objection.

Source: https://docs.diagrid.io/operate/hosting/enterprise-self-hosted/production-planning/

### 6. Logging in and proving who your app is: still basic

**What it means:** Your app proves it is allowed to talk to Catalyst with a single long-lived password-like token (`DAPR_API_TOKEN`). There is no documented way to rotate it automatically or to use "workload identity" (where the cloud vouches for your app instead of a stored secret). For humans using the console: single-sign-on federation only arrived in July–August 2026, and there is no SCIM (automatic user provisioning/de-provisioning). Free tier allows 3 users; self-hosted allows 10 per region.

**Why it matters:** Identity teams will want token rotation and SSO on day one. Plan to rotate the token yourself via your cloud's secret manager.

Source: https://docs.diagrid.io/operate/platform-operations/identity-and-access/

### 7. It is a small, young company and a very young library

**What it means:** Diagrid was founded in 2021 by the creators of Dapr. Public funding is a $24.2M Series A from 2022, with no later round found. The `diagrid` Python package first appeared on PyPI in **March 2026**; the GitHub repo has 3 contributors and single-digit stars. Releases are fast and sometimes breaking (a control-plane database migration with no upgrade path, a trial tier removed, networking settings that cannot be changed after creation).

**Why it matters:** "What if they disappear?" is a fair question. The good answer is that Catalyst is built on open-source Dapr, so you can self-host Dapr with mostly the same code. The catch is friction #1: the runner library itself is not open source until 2030.

Sources: https://www.cbinsights.com/company/diagrid ; https://github.com/diagridio/python-ai ; https://pypi.org/project/diagrid/#history

### 8. Corporate proxies and long-lived connections

**What it means:** Your app keeps one long-running connection open to Catalyst to receive work. Corporate proxies often kill idle connections after a while, and some inspect TLS traffic. The gRPC library does respect the standard `HTTPS_PROXY` / `NO_PROXY` settings, but Diagrid publishes no guidance on proxies, and the Dapr Python SDK does not send keep-alive pings by default (an open GitHub issue since July 2025).

**Why it matters:** This is the kind of thing that works on a laptop and fails mysteriously in the data center. Test it against your real proxy in week one.

Source: https://github.com/dapr/python-sdk/issues/813

### 9. "Six dependencies" is really about 144

**What it means:** The app lists six packages. But `diagrid[langgraph]` drags in `dapr-agents`, which drags in the OpenAI, Anthropic, and Hugging Face client libraries whether you use them or not. A fresh install is about 144 packages.

**Why it matters:** Your software-bill-of-materials and vulnerability scanner will see all 144. Also, Python must be 3.11 to 3.13.

Source: `pip freeze` after installing `requirements.txt` in this repo.

### 10. Outbound-only has a boundary

**What it means:** Running workflows and *publishing* events are outbound-only: your app opens the connection and pulls work. But the moment you *subscribe* to a topic, use input bindings, or use service invocation, Catalyst has to reach *into* your app, and you must allowlist Diagrid's egress IP inbound.

**Why it matters:** The demo stays on the safe side (publish, never subscribe). Do not let a future feature quietly cross that line without a new firewall conversation.

Source: https://docs.diagrid.io/develop/connect/

## Smaller things worth knowing

- **Free-tier limits:** 3 projects, 10 apps, 3 users, 512 MB per store, 100 requests per second per app, 100k requests per day per project, no SLA. Fine for a proof of concept, not for a fleet.
- **Not every Dapr API is there:** Catalyst does not offer Dapr Actors, Secrets, Configuration, or Distributed Lock. "Same code on self-hosted Dapr" holds for state, pub/sub, and workflows, not for everything.
- **The "10x faster" claim** is Catalyst versus open-source Dapr, measured by Diagrid. It is not a comparison against other products.
- **Replay is a new mental model:** durable workflows *replay* your orchestration code on resume and return stored results for finished steps. Budget one team session on this before your first incident, not during it.
- **Google Places, the demo's input:** returns up to 5 reviews per place, needs a billed GCP project, and its terms forbid storing review text. Yelp Fusion (the original plan) has no free tier anymore ($229/month minimum, review text from $299/month) and caps storage of Yelp content at 24 hours.

## So what is the honest pitch?

Use Catalyst's free tier to get a durable agent running in a sandbox in an afternoon, with a security story that fits in one sentence ("outbound 443 to three domains"). Use that working demo to earn the conversation about the vendor review. Go into that conversation already knowing the ten points above and having asked Diagrid the license question in writing. If the answers come back wrong, the same LangGraph code runs on self-hosted open-source Dapr Workflows, which is a better fallback than most agent-infrastructure startups can offer.
