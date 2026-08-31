# CaseSentinel

**District-wide IDEA compliance, watched continuously.**

CaseSentinel is a governed, multi-agent system that watches a school district's
IDEA special-education compliance posture across every caseload, flags timeline
drift before it becomes a state finding, drafts the required documents, and **proves
a named human approved every consequential action**.

Built for the **All Things Agentic** hackathon (Google / Devpost) — track: Fortified
Enterprise Fleet. Stack: **Google ADK 2.8 + Gemini 3.5 + Cloud Run + Firestore**.

🔗 **Live demo (Cloud Run):** https://casesentinel-285407834862.us-central1.run.app

> ⚠️ **Synthetic data only.** CaseSentinel ships with a generated fake district
> (Willow Creek USD) and **never** uses real student records. For special education
> — where PII handling is the core risk — synthetic-only is a maturity signal, not a
> limitation. See [Data](#data).

---

## The gap it fills

Two layers already exist and neither closes the gap (see [`RESEARCH.md`](RESEARCH.md)
for the evidence):

- **Systems of record** (Frontline, PowerSchool Special Programs, SEIS, Embrace,
  SameGoal, SpedTrack) store IEPs and track timelines — but monitor per-student or
  via periodic reports, not as a live district-wide watch.
- **AI drafting tools** (MagicSchool, Playground IEP, Brisk, Lessi, SPEDScribe)
  draft components for one teacher — but require copy-paste into the system of
  record and ship **no governed human-approval trail**.

CaseSentinel targets the three unserved gaps, each independently validated by
research: **continuous district-wide drift monitoring**, a **provable
human-approval audit trail** (EdWeek documents this only as an unmet liability
concern — "cannot prove a human was in the loop"), and eliminating the **copy-paste
seam**.

---

## Architecture

See [`docs/00-architecture-diagram.md`](docs/00-architecture-diagram.md) for the
full diagram. In short: a **supervisor** delegates **sequentially** to four
specialized sub-agents, guards the risky one, recovers from failure, and logs every
step to an append-only audit trail. No agent takes a binding action.

| Agent | Job | Model |
|---|---|---|
| **Timekeeper** | drift across all caseloads (deterministic) | — |
| **Evidence Ingestor** | normalize messy source docs | `gemini-3.5-flash-lite` |
| **Document Drafter** | draft a measurable IEP goal (guarded) | `gemini-3.5-flash` |
| **Compliance Reporter** | district posture vs. state indicators | — |

Agent contracts: [`docs/02-agent-contracts.md`](docs/02-agent-contracts.md).
Failure-recovery mechanism: [`docs/01-architecture.md`](docs/01-architecture.md).

### The signature feature — failure detection & recovery
Break a worker on camera and watch the supervisor handle it:
- **loop** (runaway) → iteration cap kills it → reroute to a healthy fallback
- **hallucination** (wrong student / non-measurable goal) → content judge rejects it
  → reroute
- **tool_error** (crash) → retry once → reroute if it persists
- **transient tool_error** → retry once → **recovers on the same worker**
- fallback also fails → **escalate to a human** (`needs_human`)

Every episode writes one structured **incident** (`fault_type`, `detection`,
`action_taken`) plus the full trace.

---

## Quick start (local, offline — no API key needed)

Requirements: Python 3.12, Node 24.

```bash
# 1) API (FastAPI + agents)
python3.12 -m venv apps/api/.venv
apps/api/.venv/bin/pip install -e "apps/api[dev]"

# 2) Dashboard
npm --prefix apps/web install

# 3) Run both (two terminals)
npm run dev:api      # http://localhost:8000
npm run dev:web      # http://localhost:5173
```

Open http://localhost:5173, choose a fault in **"Break an agent"**, and click **Run
compliance sweep** to watch the live trace, recovery, and approval gate. Offline,
the agents use a deterministic scripted model so the whole demo runs with **zero
rate-limit risk**.

### Optional — live Gemini
```bash
cp .env.example apps/api/.env
# add GOOGLE_API_KEY=... from https://aistudio.google.com/apikey
```
The Evidence Ingestor and Document Drafter then call `gemini-3.5-flash(-lite)`.

### Terminal-only spike (the failure-recovery core)
```bash
apps/api/.venv/bin/python -m casesentinel.spike.run_spike
```

---

## Deploy to Google Cloud (Cloud Run + Firestore)

The repo is deploy-ready (single-container [`Dockerfile`](Dockerfile) builds the
dashboard and serves it from FastAPI; `STORE_BACKEND=firestore` swaps the store).
These steps require **your** `gcloud` auth and a GCP project with billing enabled:

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud services enable run.googleapis.com firestore.googleapis.com

# Firestore (native mode), once per project:
gcloud firestore databases create --location=nam5

# Build + deploy the container:
gcloud run deploy casesentinel \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars STORE_BACKEND=firestore,FIRESTORE_PROJECT_ID=<YOUR_PROJECT_ID>,GOOGLE_API_KEY=<KEY>
```

Cloud Run returns a public URL serving both the dashboard and the API. Free tiers
cover demo scale; a billing card is required on the project.

---

## Mandated Google tech — and why each is here (non-decorative)

| Requirement | Used as | Justification |
|---|---|---|
| **Gemini 3.5+** | `gemini-3.5-flash` (drafting), `-flash-lite` (ingestion) via `google-genai` | the drafting + normalization intelligence |
| **Google ADK 2.8** (agent framework) | `LlmAgent`, `BaseAgent`, `Runner`, callbacks, `LoopAgent` primitives | the supervisor/sub-agent runtime and the guard hooks |
| **Cloud Run** | single-container deploy | hosts the app; `--source .` build |
| **Firestore** | append-only audit log + approvals + state | the due-process record; swaps in behind the `Store` interface |

Productionization path (described, not built for the hackathon): Agent Registry
(district-wide discovery), Agent Runtime (long-running sweeps), Memory Bank
(year-long per-case context), Agent Identity (FERPA caseload boundary), Model Armor
(screen inbound parent/provider email), Agent Observability (OTel = the paper trail).

---

## Testing

```bash
npm test              # API: pytest (agents, guards, approval gate, pipeline, recovery)
npm run build         # dashboard: TypeScript typecheck + bundle
npm run lint          # dashboard: oxlint
```

Coverage: **29 tests** (28 passing + 1 live-Gemini test that skips without a key)
across M0–M3 — the failure-recovery core, the four agents, the append-only approval
gate, the full pipeline, and each injected fault's detect → recover → log path. The
dashboard was verified live in-browser (see [`docs/03-demo-script.md`](docs/03-demo-script.md)).

---

## Repository layout

```
apps/api/    FastAPI + ADK agents (Python 3.12)
  src/casesentinel/
    agents/     timekeeper · evidence_ingestor · document_drafter · compliance_reporter
    guards/     supervisor · loop_guard · callbacks · judge · failure_injection
    approval/   gate.py (human sign-off, first-class)
    store/      base · local_store · firestore_store · factory
    audit/      append-only log + incidents
    data/       synthetic district generator + fixture
    api/        FastAPI app (REST + SSE)
    spike/      terminal demo + live-Gemini smoke
  tests/
apps/web/    Vite + React + TS + Tailwind dashboard
docs/        architecture diagram · architecture · agent contracts · demo script
PLAN.md · PROJECT.md · RESEARCH.md
```

---

## Data

All data is synthetic, generated by `casesentinel.data.generate` (seeded, so it's
reproducible): 4 schools, 8 case managers, 40 caseloads across the 13 IDEA
disability categories, deliberately seeded timeline violations (8 overdue + 10
due-soon), and messy source documents for the Evidence Ingestor. Regenerate with:

```bash
apps/api/.venv/bin/python -m casesentinel.data.generate
```

---

## Status

| Milestone | Status |
|---|---|
| M0 — failure-recovery spike (ADK 2.8) | ✅ |
| M1 — scaffold, synthetic data, dashboard shell | ✅ |
| M2 — five-agent pipeline + approval gate | ✅ |
| M3 — failure-recovery subsystem | ✅ |
| M4 — director dashboard (live) | ✅ |
| M5 — deploy-ready + docs | ✅ **live on Cloud Run + Firestore** (https://casesentinel-285407834862.us-central1.run.app); demo video pending |
