# CaseSentinel — Build Plan

> A governed, multi-agent system that watches a school district's IDEA special-education compliance posture across every caseload, flags timeline drift before it becomes a state finding, drafts required documents, and proves a named human approved every consequential action.
>
> **Hackathon:** All Things Agentic (Google / Devpost) · **Deadline:** 2026-08-31, 5:00 PM PT · **Planning date:** 2026-08-29
> **Track:** Fortified Enterprise Fleet · **Synthetic data only — never real student records.**

---

## Viability Summary

| | |
|---|---|
| **Market** | crowded-with-gap — SORs + AI drafters exist; nobody does district-wide *continuous, governed* monitoring with an approval audit trail |
| **Feasibility** | medium (2-day) — the spike is the supervisor's detect → kill → reroute → log loop on ADK 2.8 (released 3 days ago) |
| **Free to build** | yes — $0 at demo scale (Gemini + Cloud Run + Firestore free tiers); GCP billing card required |
| **Monetization** | portfolio/hackathon (commercial: per-student district license, ~$5–15/student/yr) |

Full evidence in [`RESEARCH.md`](RESEARCH.md).

---

## Research Findings

### Competitors
| Name | Pricing | Strength | Limitation |
|---|---|---|---|
| PowerSchool Special Programs | opaque ("contact sales") | Embedded AI (PowerBuddy) + "Compliance at a Glance" | Periodic/report monitoring, not continuous; no approval audit log |
| Frontline IEP | opaque | Entrenched SIS-integrated tracking | Per-student, not district drift; usability complaints |
| SEIS / EdPlan / SameGoal / Embrace / SpedTrack | opaque | Storage + state reporting | Validate form-completeness, not content or drift |
| MagicSchool / Playground IEP / Brisk / Lessi / SPEDScribe | freemium/seat | Fast drafting | Per-teacher; **no write-back to SOR** (paste only) |

**Positioning: crowded-with-gap.** The unserved wedge, each independently evidenced:
1. **Continuous district-wide drift monitoring** (validated by paid DIY tracker-spreadsheet marketplace).
2. **Governed human-approval audit trail** (EdWeek: exists only as an unmet liability concern — "cannot prove a human was in the loop").
3. **Write-back to the system of record** (whole AI layer is copy-paste today).

### Feasibility
- **Hardest part (the spike):** supervisor detects a looping/hallucinating sub-agent → kills → reroutes → writes an incident to the audit log. Primitives exist but don't compose automatically. → **Milestone 0 proves it before scaffolding.**
- **Cost flags:** none — $0 at demo scale. Free-tier RPM (5–15) means run sub-agents **sequentially**, not concurrently.

### Monetization
Portfolio/hackathon. Commercial path = per-student annual district license sold top-down to the LEA (community distribution is closed — r/specialed bans tool marketing).

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ADK 2.8.0 (released 2026-08-26) API still shifting | med | high | **Pin `google-adk==2.8.x`**; build against live docs; M0 proves the API surface before committing |
| `transfer_to_agent`-to-parent broken for sub-agents ([#4110](https://github.com/google/adk-python/discussions/4110)) | med | high | M0 uses the **exception/`escalate` + supervisor-dispatch** pattern, not child→parent transfer |
| Free-tier RPM (5–15) throttles a live multi-agent run | high | high | Run sub-agents **sequentially**; use `gemini-3.5-flash-lite` for cheap agents; pre-seed results + have a **recorded backup demo** |
| No stable `gemini-3-pro` | high | low | Target `gemini-3.5-flash` / `gemini-3.5-flash-lite` (satisfies "3.5 or newer") |
| Firestore requires GCP billing card | med | med | Storage behind an interface with a **local JSON/SQLite adapter**; core demo never blocks on the network |
| `before_model_callback` crash on Vertex Agent Engine ([#3798](https://github.com/google/adk-python/discussions/3798)) | low | med | **Deploy to Cloud Run, not Agent Engine** |
| 2-day scope overrun | high | high | Milestones ordered so the **signature demo (M0–M3) is done before the dashboard (M4)**; M5 deploy is stretch |

---

## Tech Stack

> Versions verified against official docs/PyPI/npm on **2026-08-29**. Re-check before coding (the plan's standing rule).

| Layer | Choice | Version | Reason |
|---|---|---|---|
| Language (backend/agents) | **Python** | 3.12 | ADK is Python-first; required by the framework |
| Agent framework | **Google ADK** | `google-adk` **2.8.x** (pin exactly) | Mandated. Supervisor + sub-agents; `adk deploy cloud_run`. Released 2026-08-26 — pin it |
| LLM | **Gemini** via `google-genai` | `gemini-3.5-flash` (reasoning), `gemini-3.5-flash-lite` (screening/ingestion) | Mandated ("3.5 or newer"). Use the current `google-genai` SDK, **not** deprecated `google-generativeai` |
| API server | **FastAPI** + Uvicorn | ~0.141 | ADK integrates with FastAPI; serves REST + SSE trace stream; single Cloud Run service |
| State + audit log | **Firestore** (behind a `Store` interface with a local JSON/SQLite adapter) | latest | Mandated GCP infra service; visible "DB updates" in demo; local adapter keeps the demo network-independent |
| Observability | **OpenTelemetry** (ADK-native) → console + Firestore | ADK 2.8 built-in | The reasoning trace **is** the due-process paper trail; justifies Agent Observability |
| Frontend | **Vite + React + TypeScript** | Vite 8.1.x, React 19.x | Internal tool, no SEO; SPA over FastAPI REST/SSE; avoids a second (Node) runtime alongside Python |
| Styling/UI | **Tailwind CSS** (+ a few shadcn/ui components) | Tailwind 4.3.x | Polished dashboard fast for the 30% demo-readiness rubric |
| Hosting | **Cloud Run** (backend + built static frontend as one service) | — | Mandated GCP infra; one-command `adk deploy cloud_run`. **Stretch — local-first per scope decision** |
| Synthetic data | Python generator script (Faker) | latest | Fake district with seeded violations + messy docs |

**Deliberately skipped (with reason):**
- **Auth** — single-director demo; note as non-goal. (Agent Identity / FERPA boundary is *described* in the README as the productionization path, and simulated via a `case_manager_id` scoping check, not a real IdP.)
- **Pub/Sub** — sequential orchestration for the demo; adds failure surface with no demo payoff. Named in README as the async-scale path.
- **npm/pnpm workspaces** — one app; root `package.json` delegates.
- **Next.js** — no SSR/SEO need; would add a Node runtime beside Python.
- **Payments** — not applicable.

**Google Cloud / Gemini Enterprise services — mapped to non-decorative justifications (for the README):**
| Service | Used as | Justification |
|---|---|---|
| Cloud Run | deploy target | required infra; hosts the ADK app |
| Firestore | state + audit log | required infra; the due-process record |
| Agent Observability (OTel) | reasoning traces | the audit paper trail judges can inspect |
| Model Armor | Correspondence Screener guardrail (**stretch**) | screens inbound parent/provider email for prompt injection/PII |
| Memory Bank | per-case context (described; simulated via Firestore per-case docs) | year-long case continuity |
| Agent Identity | caseload scoping (simulated via `case_manager_id` check) | FERPA boundary — one caseload can't read another |
| Agent Registry / Runtime / Gateway | described in README as productionization | district-wide discovery, long-running execution, policy routing |

---

## Project Structure

```
CaseSentinel/
├─ apps/
│  ├─ api/                      # Python: ADK agents + FastAPI (its own pyproject/requirements)
│  │  └─ src/casesentinel/
│  │     ├─ agents/             # one module per agent
│  │     │  ├─ supervisor.py    # orchestrator: delegate, monitor, detect, reroute, log
│  │     │  ├─ timekeeper.py    # deadline drift across caseloads
│  │     │  ├─ evidence_ingestor.py
│  │     │  ├─ document_drafter.py   # PLAAFP/goals/PWN/BIP
│  │     │  ├─ compliance_reporter.py
│  │     │  └─ correspondence_screener.py   # stretch (Model Armor)
│  │     ├─ guards/             # failure detection + recovery
│  │     │  ├─ callbacks.py     # before/after_model_callback guardrails + judge
│  │     │  ├─ loop_guard.py    # iteration caps / runaway detection
│  │     │  └─ failure_injection.py   # REAL, testable fault injection (loop/hallucination/tool-error)
│  │     ├─ approval/           # human approval gate as a first-class object
│  │     │  └─ gate.py          # ApprovalRequest lifecycle: pending→approved/rejected
│  │     ├─ store/              # storage abstraction
│  │     │  ├─ base.py          # Store interface (audit, approvals, cases, incidents)
│  │     │  ├─ firestore_store.py
│  │     │  └─ local_store.py   # JSON/SQLite fallback
│  │     ├─ audit/              # append-only audit log + incident records
│  │     ├─ api/                # FastAPI routes + SSE trace stream
│  │     └─ data/               # synthetic district generator + seeded fixtures
│  └─ web/                      # Vite + React + TS dashboard (own package.json)
│     └─ src/
│        ├─ app/                # routes/pages
│        ├─ features/           # caseload-grid, drift-alerts, approvals, audit-log, agent-trace, break-agent
│        └─ lib/                # api client, SSE hook, types
├─ docs/                        # 01-architecture.md, 02-agent-contracts.md, 03-demo-script.md, ...
├─ PROJECT.md                   # living context tracker
├─ PLAN.md                      # this file
├─ RESEARCH.md                  # market/feasibility evidence
├─ package.json                 # root: delegating scripts (npm --prefix apps/web ...)
├─ .env.example
├─ CLAUDE.md                    # one line → PROJECT.md
└─ README.md                    # spin-up, architecture diagram, synthetic-data disclaimer, GCP proof
```

**Conventions**
- `apps/<name>` even for one app of each kind; root `package.json` delegates, no workspaces until a 2nd JS package exists.
- Each agent has a written **contract** (inputs, outputs, tools, failure modes) in `docs/02-agent-contracts.md` — this is the "strict separation of concerns" the 30% rubric rewards.
- `docs/` filenames: zero-padded kebab-case.
- **Before coding against ADK / `google-genai` / Firestore / Vite, fetch the latest official docs.** ADK 2.8 is 3 days old — never code its API from memory.
- Keep `PROJECT.md` in sync whenever structure, stack, status, or a decision changes.

---

## Environment Variables

```
# Required
GOOGLE_API_KEY=            # Gemini API key from AI Studio (free tier)
GEMINI_MODEL_MAIN=gemini-3.5-flash        # supervisor + drafter
GEMINI_MODEL_LITE=gemini-3.5-flash-lite   # ingestor + screener

# Storage (local-first; flip to firestore for the deploy stretch)
STORE_BACKEND=local        # local | firestore
FIRESTORE_PROJECT_ID=      # only if STORE_BACKEND=firestore
GOOGLE_APPLICATION_CREDENTIALS=   # path to service-account JSON (deploy only)

# Demo controls
FAILURE_INJECTION_ENABLED=true    # enables the "break an agent" endpoint for the live demo
```

---

## Milestones

> Ordered so the **signature demo (M0–M3) is complete before the dashboard**. If time runs short, M4 shrinks and M5 is dropped — the failure-recovery moment still exists and is demoable from the terminal.

### Milestone 0: Spike — prove the kill/reroute/log loop *(do this FIRST)*
**Goal:** In a terminal, a supervisor delegates to one sub-agent; when that sub-agent is forced to loop or hallucinate, the supervisor detects it, stops it, reroutes to a fallback path, and writes an incident record — all on ADK 2.8 + real Gemini.

Tasks:
- [x] Install and pin `google-adk==2.8.0` and current `google-genai` (2.20.0); confirm a minimal `LlmAgent` makes a real `gemini-3.5-flash` call — Done when: a one-agent script prints a Gemini response _(script `spike/smoke_gemini.py` + skipped-without-key test built and verified against ScriptedLlm; live call pending the user's `GOOGLE_API_KEY`)_
- [x] Build a supervisor with one sub-agent using the current ADK 2.8 delegation pattern (verified against installed 2.8.0 API) — Done when: supervisor routes a task to the sub-agent and returns its result
- [x] Implement **loop detection**: iteration cap trips on a deliberately looping sub-agent (`LoopingWorker`), generator `aclose()`d on kill — Done when: a forced-loop run halts at the cap instead of running forever
- [x] Implement **bad-output detection** via `guards/judge.py` heuristic (wrong-student + non-measurable) on a deliberately hallucinated goal — Done when: the judge flags the bad output and the supervisor treats it as a fault
- [x] Implement **recovery**: supervisor catches fault/exception and dispatches to a fallback agent, else a "needs human" path (NOT `transfer_to_agent`-to-parent) — Done when: after a fault, control returns to the supervisor and an alternative path runs
- [x] Write the incident to an append-only audit record (local store) — Done when: the run leaves a JSON incident with {agent, fault_type, detection, action_taken, timestamp}
- [x] `docs/01-architecture.md` first draft capturing the proven mechanism — Done when: the detect→kill→reroute→log sequence is documented with the exact ADK primitives used
- [x] Gate: a `pytest` test injects each fault (loop, hallucination, tool-error) and asserts detection + recovery + audit entry — Done when: all green _(6 passed, 1 skipped)_

### Milestone 1: Scaffold
**Goal:** Repo runs locally; structure, deps, synthetic data, storage, and audit primitives in place.

Tasks:
- [x] Create `apps/api` (Python 3.12, `pyproject.toml`, pinned deps) and `apps/web` (Vite 8.2 + React 19.2 + TS 6 + Tailwind 4.3) — Done when: `uvicorn` serves `/health` 200 and `npm --prefix apps/web run dev` starts clean _(both verified; Vite proxies /api → :8000 end-to-end)_
- [x] Root delegating `package.json` (`dev:web`, `dev:api`, `build`, `lint`, `test`) + `.env.example` — Done when: committed
- [x] Implement `store/base.py` interface + `local_store.py` (JSONL/in-memory) — Done when: audit/approval/case CRUD round-trips in a unit test _(M0)_
- [x] Implement append-only `audit/` log used by M0's incident writer — Done when: entries are immutable-append and timestamped (unit test) _(M0)_
- [x] Synthetic district generator (`data/`): 4 schools, 40 caseloads, 13 disability categories, **seeded timeline violations** (8 overdue + 10 due-soon), and 6 **messy source docs** — Done when: `python -m casesentinel.data.generate` writes a deterministic fixture and a test asserts ≥1 seeded violation exists
- [x] Create `PROJECT.md` + one-line `CLAUDE.md` — Done when: PROJECT.md describes purpose, stack+versions, structure, conventions, status
- [x] Gate: lint + typecheck + tests pass — Done when: all green _(api 12 passed/1 skipped; web build+lint clean)_

### Milestone 2: Core multi-agent system
**Goal:** The five agents run under the supervisor on synthetic data, producing real outputs, every consequential output routed through the approval gate and written to the audit log.

Tasks:
- [x] Write `docs/02-agent-contracts.md` (inputs/outputs/tools/failure modes per agent) — Done when: all agents specified with no open questions
- [x] **Timekeeper**: scans caseloads, computes days-to-deadline, emits drift alerts (deterministic) — Done when: it flags the seeded violations with severity, unit-tested _(most-urgent-first, all 4 deadline types)_
- [x] **Evidence Ingestor**: normalizes messy docs into a structured evidence object (`gemini-3.5-flash-lite`; deterministic offline) — Done when: a messy fixture yields a clean record, unit-tested
- [x] **Document Drafter**: goal draft from ingested evidence (`gemini-3.5-flash`; scripted offline) — Done when: given evidence, returns a draft _(guarded; evidence-aware instruction)_
- [x] **Compliance Reporter**: rolls caseload status into a district posture summary vs. state indicators — Done when: returns a district-level rollup object, unit-tested _(totals add up to caseload size)_
- [x] **Approval gate** (`approval/gate.py`): every Drafter output creates a `pending` ApprovalRequest; approve/reject transitions write to the audit log with the named approver — Done when: state machine unit-tested (pending→approved/rejected; double-decide rejected) _(append-only, state folded from immutable records)_
- [x] Supervisor orchestrates the full pipeline **sequentially** (RPM-safe) and logs every step via audit — Done when: pipeline produces alerts + a draft + an approval request + a posture report, all under one `run_id` _(`orchestrator.py`; `POST /api/run`)_
- [x] Gate: lint + typecheck + tests + one E2E happy-path test of the full pipeline — Done when: all green _(21 passed, 1 skipped; live HTTP smoke of run/approve/decide/incidents)_

### Milestone 3: Failure detection & recovery (the signature feature)
**Goal:** The M0 spike, generalized into a real, testable subsystem the supervisor applies to every sub-agent, triggerable live.

Tasks:
- [x] `guards/failure_injection.py`: a real feature to inject a **loop**, a **hallucinated goal**, a **tool-error**, or a **transient tool-error** into the drafter — Done when: `POST /api/run?fault=` reproducibly breaks it _(4 injectable faults; drafter is the injectable target — deterministic agents can't loop/hallucinate)_
- [x] Generalize `guards/loop_guard.py` (execution: loop/crash) + `guards/callbacks.py` (content judge) so the supervisor monitors **any** sub-agent — Done when: any injected fault is detected regardless of agent _(guard is agent-agnostic; unit-tested on generic workers)_
- [x] Supervisor recovery policy: kill, then **retry-once for transient faults / reroute for systematic faults / escalate to human if the fallback also fails**, writing one structured **incident** with `action_taken` — Done when: each fault type yields the correct action + incident
- [x] Expose the incident + trace over the API — Done when: `GET /api/incidents` and `GET /api/runs/{run_id}/trace` return the recovery events _(live SSE stream added in M4)_
- [x] Gate: E2E tests injecting all fault types assert detect → kill → retry/reroute/escalate → incident-logged — Done when: all green _(28 passed, 1 skipped; live HTTP smoke)_

### Milestone 4: Web dashboard (the demo surface)
**Goal:** A director can see district posture, drift alerts, live agent reasoning, approve/reject a draft, read the audit log, and **break an agent on camera**.

Tasks:
- [x] API client + SSE hook in `apps/web/src/lib` — Done when: the app streams live trace events from the running backend _(EventSource `/api/run/stream`)_
- [x] **District overview + caseload grid** with color-coded drift status (Overdue/Due-Soon/Compliant) — Done when: seeded violations render with correct status from live data _(+ at-risk-only filter)_
- [x] **Live agent-trace panel** (SSE) showing supervisor delegation + sub-agent steps — Done when: running the pipeline streams steps in real time _(paced, human-readable summaries, auto-scroll)_
- [x] **Approval-gate panel**: view a Drafter draft, Approve/Reject with approver name → writes audit entry, UI reflects new state — Done when: the click path approves a draft and it persists to Decided _(verified live: Finn Novak approved by Dr. Alvarez)_
- [x] **Incident viewer** — Done when: recovery incidents are visible with fault type, detection, and action taken
- [x] **"Break an agent" control** wired to failure injection — Done when: clicking it triggers a fault and the trace panel shows the supervisor detecting, killing, rerouting, and logging — live _(verified on camera: hallucination → reject → kill → reroute → resolved)_
- [x] `docs/03-demo-script.md`: the ≤4-min unedited run (incl. the failure moment) — Done when: a step-by-step script produces the whole story
- [x] Gate: lint + typecheck + tests; manual click-path in demo script verified — Done when: all green _(web build+lint clean; api 28 passed/1 skipped; live browser verification)_

### Milestone 5: Deploy + submission polish *(stretch — local-first per scope)*
**Goal:** Live on Google Cloud with visible proof, plus every deliverable ready.

Tasks:
- [x] `STORE_BACKEND=firestore` support — Done when: the store factory swaps LocalStore↔FirestoreStore behind the interface _(`store/firestore_store.py` + `store/factory.py`; lazy GCP import; unit-tested)_. **Provisioning a live Firestore needs the user's GCP project.**
- [x] Single Cloud Run container serving built React static from the FastAPI service — Done when: one process serves the dashboard and `/health` returns 200 _(verified locally: `/`→200 html, `/health`→200; `Dockerfile` + `.dockerignore`)_. **`gcloud run deploy` needs the user's `gcloud` auth.**
- [x] Architecture diagram (agents, supervisor, guards, approval gate, store, GCP services) — Done when: committed to `docs/` and README _(`docs/00-architecture-diagram.md`, mermaid)_
- [x] README: spin-up, env vars, **synthetic-data disclaimer**, deploy steps, and the non-decorative justification for each Google service — Done when: a fresh reader can run it from scratch
- [ ] Record ≤4-min demo → public YouTube/Vimeo — **needs the user** (screen recorder + account); script ready in `docs/03-demo-script.md`
- [ ] Bonus (+): public build writeup; social post with `#AllThingsAgenticHackathon` — **needs the user**

---

## Claude Code Commands

> Every session: fetch the latest official docs for any library before coding (ADK 2.8 especially), and keep `PROJECT.md` in sync.

**Start (Milestone 0 — the spike):**
```
claude "Read PLAN.md, PROJECT.md, and RESEARCH.md. Complete Milestone 0 only — prove the supervisor detect/kill/reroute/log loop on ADK 2.8 + Gemini, fetching the latest official ADK and google-genai docs first. Update PROJECT.md. Mark tasks done as you go. Stop after M0 and commit."
```

**Resume from any point:**
```
claude "Read PLAN.md and PROJECT.md. Find the first incomplete task and continue, fetching the latest official docs for any library before using it. Keep PROJECT.md in sync. Mark tasks done as you go. Commit when a milestone is complete."
```

**Test current state:**
```
claude "Read PLAN.md and PROJECT.md. Without building anything new, run all tests and the demo pipeline. Report what works and what's broken."
```

---

## Notes & Decisions

- **2026-08-29** — Scope locked to the signature failure-recovery demo (win condition), a web dashboard, local-first with GCP deploy as stretch. Rationale: 2-day clock; the "break a worker agent, supervisor recovers" moment is the differentiator almost no submission has.
- **2026-08-29** — 5 core agents (Supervisor, Timekeeper, Evidence Ingestor, Document Drafter, Compliance Reporter); Correspondence Screener is stretch. Enough to be credibly multi-agent and to make the failure demo land.
- **2026-08-29** — Recovery uses supervisor-side catch/dispatch, NOT `transfer_to_agent`-to-parent (reported broken for sub-agents, [#4110](https://github.com/google/adk-python/discussions/4110)).
- **2026-08-29** — Sub-agents run sequentially to stay under free-tier RPM; a recorded backup demo hedges live rate-limit risk.
- **2026-08-29** — Storage behind an interface (local JSON/SQLite default, Firestore for deploy) so the core demo never blocks on the network or a billing card.
- **2026-08-29** — Deploy to Cloud Run, not Vertex Agent Engine (`before_model_callback` crash reported on Agent Engine, [#3798](https://github.com/google/adk-python/discussions/3798)).
