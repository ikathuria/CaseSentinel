# CaseSentinel — Project Tracker

> Living context map. Any LLM or human should be able to read this file alone and understand
> what the project is, how it's built, and where things are. **Keep it in sync** — update it
> whenever the stack, structure, conventions, or status changes.

_Last updated: 2026-08-29 (Milestone 0 complete — failure-recovery spike proven)_

---

## What it is

CaseSentinel is a governed, multi-agent system that continuously watches a school district's IDEA special-education compliance posture across every caseload. It flags timeline drift (evaluation, re-evaluation, annual review, secondary-transition deadlines) before it becomes a state finding, drafts the required documents (PLAAFP, IEP goals, Prior Written Notice, Behavior Intervention Plan) from source evidence, and proves that a named human approved every consequential action via an append-only audit log. The buyer is a school district / special-education cooperative (LEA); the primary user is a special-education director or compliance coordinator. **Hard rule: no agent makes a binding decision — every consequential output is a recommendation routed to a named human approver.** Built for the All Things Agentic hackathon (Google/Devpost). **Synthetic student data only.**

The differentiator (validated in [`RESEARCH.md`](RESEARCH.md)): existing tools are either systems of record or per-teacher AI drafters. Nobody runs district compliance as a live, governed, agentic system. The signature demo is deliberately **breaking a worker agent on camera** (loop / hallucination) and showing the supervisor detect it, kill it, reroute, and log the incident.

---

## Stack

| Layer | Choice | Version | Notes |
|---|---|---|---|
| Language (backend/agents) | Python | 3.12 | ADK is Python-first |
| Agent framework | Google ADK | `google-adk` 2.8.x (pin) | Mandated; released 2026-08-26 — build against live docs |
| LLM | Gemini via `google-genai` | `gemini-3.5-flash` + `gemini-3.5-flash-lite` | Mandated; NOT the deprecated `google-generativeai` |
| API server | FastAPI + Uvicorn | ~0.141 | REST + SSE trace stream; one Cloud Run service |
| State + audit log | Firestore behind a `Store` interface (+ local JSON/SQLite adapter) | latest | Mandated GCP infra; local adapter keeps the demo offline-safe |
| Observability | OpenTelemetry (ADK-native) | ADK 2.8 | The trace = the due-process paper trail |
| Frontend | Vite + React + TypeScript | Vite 8.1.x, React 19.x | SPA over FastAPI; no second runtime |
| Styling | Tailwind CSS (+ some shadcn/ui) | Tailwind 4.3.x | Fast, polished dashboard |
| Hosting | Cloud Run | — | `adk deploy cloud_run`; **stretch (local-first)** |

> Versions verified against official docs/PyPI/npm on 2026-08-29. Re-verify before coding — ADK especially.

---

## Architecture

1. **Supervisor (orchestrator)** receives a district-run request and delegates **sequentially** (RPM-safe) to sub-agents.
2. **Timekeeper** scans caseloads → drift alerts. **Evidence Ingestor** normalizes messy source docs → structured evidence. **Document Drafter** turns evidence into a PLAAFP/goal/PWN/BIP draft. **Compliance Reporter** rolls caseload status into a district posture summary vs. state indicators.
3. Every Drafter output becomes a **pending ApprovalRequest** (first-class object). A named human approves/rejects; the transition is written to the audit log.
4. **Guards** wrap every sub-agent: `before/after_model_callback` (output judge) + loop caps. On a fault the supervisor **kills the run, reroutes** (retry-once → fallback → "needs human"), and writes a structured **incident**.
5. **Failure injection** (env-gated, real feature) can break a chosen sub-agent to trigger the recovery path live.
6. Everything persists via the `Store` interface (local by default, Firestore on deploy); the API streams traces to the dashboard over SSE.

---

## Project structure

```
CaseSentinel/
├─ apps/
│  ├─ api/src/casesentinel/   # ADK agents + FastAPI
│  │  ├─ agents/              # supervisor, timekeeper, evidence_ingestor, document_drafter,
│  │  │                       #   compliance_reporter, correspondence_screener (stretch)
│  │  ├─ guards/              # callbacks (judge), loop_guard, failure_injection
│  │  ├─ approval/           # gate.py — ApprovalRequest lifecycle
│  │  ├─ store/              # base interface + firestore_store + local_store
│  │  ├─ audit/              # append-only audit log + incidents
│  │  ├─ api/                # FastAPI routes + SSE
│  │  └─ data/               # synthetic district generator + fixtures
│  └─ web/src/               # Vite+React dashboard: caseload grid, drift alerts, approvals,
│                            #   audit log, live agent trace, "break an agent" control
├─ docs/                     # 01-architecture, 02-agent-contracts, 03-demo-script
├─ PROJECT.md · PLAN.md · RESEARCH.md · README.md · CLAUDE.md · .env.example
└─ package.json              # root: delegating scripts
```

---

## Conventions

- **Where new code goes:** a new agent → `apps/api/src/casesentinel/agents/<name>.py` with a contract in `docs/02-agent-contracts.md`; a new dashboard view → `apps/web/src/features/<name>/`.
- **Naming:** Python snake_case modules; React features kebab-case folders.
- **Testing:** `pytest` in `apps/api` (unit tests colocated per module; E2E for the full pipeline and each fault type); Vitest for `apps/web` logic. Every milestone ends green on lint + typecheck + tests.
- **Docs:** `docs/` filenames zero-padded kebab-case.
- **Before coding any library:** fetch its latest official docs — never code APIs from memory. **ADK 2.8 is days old; this is non-optional.**
- **Design invariant:** no agent commits a consequential action; it only produces recommendations routed through the approval gate.

---

## Current status

| Milestone | Status | Notes |
|---|---|---|
| 0. Spike (detect/kill/reroute/log) | ✅ done | Proven on ADK 2.8.0; 4 scenarios green, offline. See `docs/01-architecture.md` |
| 1. Scaffold | ◐ partial | `apps/api` exists (venv, pyproject, store, audit, guards); still need `apps/web`, root scripts, synthetic-data generator |
| 2. Core multi-agent system | ☐ todo | 5 agents + approval gate, sequential orchestration |
| 3. Failure detection & recovery | ☐ todo | generalizes M0 into a real subsystem + injection API |
| 4. Web dashboard | ☐ todo | the demo surface, incl. "break an agent" |
| 5. Deploy + polish | ☐ todo | stretch — Cloud Run + Firestore + video |

**In progress now:** M0 done. `apps/api` scaffolded with the failure-recovery core.
**Next up:** Milestone 1 — finish scaffold (web app, root delegating scripts, synthetic district generator).

### What exists in `apps/api` after M0
- `models/scripted_llm.py` — offline `BaseLlm`; `models/factory.py` — Gemini-or-scripted selector
- `store/{base,local_store}.py` — append-only Store (JSONL/in-memory)
- `audit/log.py` — `AuditLog` + incident recorder
- `guards/judge.py` — heuristic goal judge; `guards/failure_injection.py` — loop/hallucination/tool_error workers; `guards/supervisor.py` — the detect/kill/reroute/log core
- `spike/run_spike.py` — terminal demo; `spike/smoke_gemini.py` — live-Gemini smoke
- `tests/` — M0 gate (6 passed, 1 skipped) · run: `cd apps/api && .venv/bin/python -m pytest -q`

---

## Decision log

- 2026-08-29 — Scope locked to the signature failure-recovery demo + web dashboard, local-first, GCP deploy as stretch — 2-day clock; the break-and-recover moment is the differentiator.
- 2026-08-29 — 5 core agents; Correspondence Screener is stretch — enough to be credibly multi-agent and land the demo.
- 2026-08-29 — Recovery via supervisor catch/dispatch, not `transfer_to_agent`-to-parent — that path is buggy for sub-agents (adk-python #4110).
- 2026-08-29 — Sequential sub-agent execution — stays under Gemini free-tier RPM; recorded backup demo hedges live throttling.
- 2026-08-29 — Storage behind an interface (local default, Firestore on deploy) — core demo never blocks on network/billing.
- 2026-08-29 — Deploy to Cloud Run, not Vertex Agent Engine — `before_model_callback` crash reported on Agent Engine (#3798).
- 2026-08-29 — Target `gemini-3.5-flash`/`-flash-lite`; no stable `gemini-3-pro` exists.

---

## Glossary

- **IDEA** — Individuals with Disabilities Education Act; the federal law mandating special-education services and their paperwork.
- **IEP** — Individualized Education Program; the legal document for a student receiving special education.
- **LEA** — Local Education Agency; the school district (the buyer/monitored entity).
- **PLAAFP** — Present Levels of Academic Achievement and Functional Performance (an IEP section).
- **PWN** — Prior Written Notice; a legally required notice to parents before certain actions.
- **BIP / FBA** — Behavior Intervention Plan / Functional Behavior Assessment.
- **RDA** — Results Driven Accountability; the state framework scoring districts on IDEA indicators.
- **Timeline drift** — a caseload approaching or past a mandated deadline (evaluation, re-eval, annual review, transition).
- **Approval gate** — the first-class object enforcing that a named human approves every consequential agent output.
- **Incident** — a structured record of a detected agent failure (loop/hallucination/tool-error) and the supervisor's recovery.
- **System of record (SOR)** — the district's IEP system (Frontline, SEIS, PowerSchool, etc.) CaseSentinel integrates with, not replaces.
