# CaseSentinel — Devpost Submission

> Paste-ready copy for the Devpost fields. Fill the **[VIDEO URL]** and **[CLOUD RUN URL]**
> placeholders before submitting. Track: **Fortified Enterprise Fleet**.

---

## Tagline
District-wide IDEA special-education compliance, watched continuously — a governed
multi-agent system that flags timeline drift, drafts the required documents, and
proves a named human approved every consequential action.

---

## Inspiration
Special education runs on legally mandated paperwork with hard deadlines. Teachers
report **15–20 unpaid hours a week** on it, ~33% annual attrition, and a single
missed IEP deadline is **federal noncompliance** that surfaces as a state audit
finding. Two tool categories already exist and neither closes the gap: **systems of
record** (Frontline, PowerSchool, SEIS) *store* IEPs; **AI drafters** (MagicSchool,
Playground IEP) *draft* text for one teacher and require copy-paste into the system
of record. Nobody runs the *district's* compliance posture as a live, monitored
system, and — per EdWeek — nobody can *prove a human was in the loop*, which is
exactly the liability that matters under IDEA. That unserved, high-stakes, clearly
multi-step problem is what we built for.

## What it does
CaseSentinel is a supervisor/orchestrator agent that delegates to four specialized
sub-agents and governs the whole workflow:
- **Timekeeper** — continuously scans every caseload and raises timeline drift
  (evaluation, re-eval, annual review, secondary transition) *before* it becomes a finding.
- **Evidence Ingestor** — normalizes messy progress notes, therapy memos, and
  behavior logs into structured evidence.
- **Document Drafter** — drafts a measurable IEP goal from that evidence.
- **Compliance Reporter** — rolls caseloads up into a district posture report
  against state-indicator-style metrics.

Two things make it different:
1. **A governed human-approval gate as a first-class object.** No agent takes a
   binding action. Every draft becomes a *pending* recommendation that only a
   **named human** can approve or reject — and every decision is written to an
   append-only audit log (the due-process trail).
2. **A failure-tolerant supervisor.** The risky agent runs under a guard; if it
   loops, crashes, or hallucinates, the supervisor detects it, kills it, and
   recovers — logging a structured incident.

A director watches all of it live on a web dashboard: posture, caseload drift, a
real-time agent trace, the approval gate, and an incident log.

## The signature feature — failure detection & recovery
You can **break a worker on demand** ("Break an agent") and watch the supervisor
handle it, with a policy tuned to the failure type:
- **Hallucination** (wrong student / non-measurable goal) → a content judge rejects
  it → **reroute** to a healthy fallback.
- **Runaway loop** → iteration cap kills it → **reroute**.
- **Transient tool error** → **retry the same worker once** → it recovers, no fallback needed.
- **Persistent tool error** → retry → **reroute**.
- **Fallback also fails** → **escalate to a human** (`needs_human`).

Every episode writes one structured incident (`fault_type`, `detection`,
`action_taken`) plus the full trace. Almost no submission builds failure injection
as a real, testable feature — we made it a first-class part of the product.

## How we built it
- **Agents & orchestration:** **Google ADK 2.8** (`LlmAgent`, `BaseAgent`,
  `Runner`, model/tool callbacks, `LoopAgent`). A supervisor delegates
  **sequentially** (RPM-safe) and monitors each worker with an agent-agnostic guard
  (`loop_guard` for execution faults + a content judge in `callbacks`).
- **Reasoning:** **Gemini 3.5** via the `google-genai` SDK — `gemini-3.5-flash` for
  drafting, `gemini-3.5-flash-lite` for evidence normalization. A deterministic
  offline model lets the whole system (and the failure demo) run reproducibly with
  zero rate-limit risk.
- **API:** **FastAPI** with a **Server-Sent Events** endpoint that streams each
  pipeline step live to the dashboard.
- **State & audit:** an append-only **Store** interface with two backends —
  local JSONL for dev, **Firestore** for the deploy.
- **Dashboard:** **Vite 8 + React 19 + Tailwind 4**.
- **Deploy:** a single-container **Dockerfile** builds the dashboard and serves it
  from FastAPI; deploys to **Cloud Run** with one command.

## Data sources
**Synthetic data only — no real student records.** A seeded generator produces a
realistic fake district (Willow Creek USD): 4 schools, 8 case managers, 40 caseloads
across all 13 IDEA disability categories, deliberately seeded timeline violations
(8 overdue + 10 due-soon), and messy source documents for the Evidence Ingestor. For
this domain, synthetic-only is a maturity signal — current guidance already tells
teachers never to put real student PII into an AI prompt.

## Challenges we ran into
- **ADK 2.8 shipped three days before we started** (Aug 26, 2026) with breaking
  changes and a new graph-execution engine — so we built against the *installed*
  API by introspecting it, not against stale tutorials, and pinned the version.
- **`transfer_to_agent` back to a parent is reported broken for sub-agents**
  (adk-python #4110), so we do recovery *supervisor-side* (catch/dispatch) instead.
- **Free-tier Gemini rate limits** are a live-demo hazard, so we run agents
  sequentially and added a deterministic offline model for a rate-limit-free demo.
- We deliberately deployed to **Cloud Run**, not Vertex Agent Engine, because a
  `before_model_callback` crash is reported on Agent Engine (adk-python #3798).

## Accomplishments we're proud of
- A genuinely **failure-tolerant** multi-agent system where recovery is a real,
  demoable feature — not a slide.
- **Human sign-off enforced as a first-class object** with an append-only, tamper-
  evident audit trail — the exact governance gap incumbents leave open.
- **Deep, honest testing:** 54 automated tests + a 59-assertion live HTTP/SSE/
  concurrency battery, 87% coverage. Our adversarial pass even caught and fixed a
  real persistence bug and a trace-accuracy bug.

## What we learned
- The market gap is real and evidenced: paid DIY "IEP deadline tracker" spreadsheets
  prove demand for continuous monitoring; EdWeek confirms the human-in-the-loop
  *proof* is an unmet liability concern.
- The hard part of multi-agent systems isn't the happy path — it's **detecting and
  recovering from a worker that loops or hallucinates**, and the ADK primitives for
  that (`max_iterations`, model/error callbacks, `escalate`) don't compose for free.
- Making the demo deterministic (offline model) was the single best decision for a
  live, unedited recording.

## What's next
Write-back into the real systems of record (SEIS/Frontline/PowerSchool), Model Armor
on inbound parent/provider email, Memory Bank for year-long per-case context, and
Agent Identity to enforce the FERPA caseload boundary.

## Built with
`google-adk-2.8` · `gemini-3.5-flash` · `gemini-3.5-flash-lite` · `google-genai` ·
`python` · `fastapi` · `server-sent-events` · `cloud-run` · `firestore` · `docker` ·
`react` · `vite` · `typescript` · `tailwindcss`

## Try it out
- **Repo:** https://github.com/ikathuria/CaseSentinel
- **Live app (Cloud Run):** https://casesentinel-285407834862.us-central1.run.app
- **Demo video:** [VIDEO URL]
- Runs locally in minutes (offline, no API key) — see the README.

---

## How this meets the judging criteria  *(for the reviewers)*

**Innovation & Operational Utility (40%)**
- Genuinely multi-agent: a supervisor intelligently delegates to four *specialized*
  sub-agents; the task (district-wide, cross-caseload compliance with drafting,
  monitoring, and governance) is too complex for a single agent.
- Built for the **"unlikely hero"** — the special-education director / compliance
  coordinator — not a procurement manager.
- Solves a real, evidenced, high-stakes problem incumbents don't.

**Architectural Discipline & Tech Stack (30%)**
- **Strict separation of concerns:** each agent has one job, a typed input/output,
  and a documented failure mode (`docs/02-agent-contracts.md`).
- **Failure-tolerant inter-agent routing:** the supervisor detects loops,
  hallucinations, and crashes, then retries / reroutes / escalates and logs an
  incident — the explicit "how does it recover from a looping or hallucinating
  worker" requirement, built and tested.

**Demo & Production Readiness (30%)**
- Unedited live execution: the video shows the pipeline, the live break-and-recover,
  DB/audit updates, and terminal logs.
- Clean architecture diagram (`docs/00-architecture-diagram.md`).
- Reproducible setup (README, one-command local run) and visible Google Cloud
  deployment (Cloud Run + Firestore).

## Mandatory requirements checklist
- [x] **Gemini 3.5+** — `gemini-3.5-flash` / `gemini-3.5-flash-lite` via `google-genai`.
- [x] **A Google agent framework** — **Google ADK 2.8** (supervisor + sub-agents, callbacks, guards).
- [x] **A Google Cloud infra service** — **Cloud Run** (deploy) + **Firestore** (audit store).
- [x] Public repo with step-by-step README.
- [x] Architecture diagram.
- [x] Synthetic data only (stated explicitly).
- [x] **Hosted URL** — https://casesentinel-285407834862.us-central1.run.app (live on Cloud Run + Firestore; verified end-to-end with live Gemini 3.5).
- [ ] ≤4-min public demo video — record with `docs/04-video-script.md`, then paste **[VIDEO URL]**.
