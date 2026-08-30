# 03 — Demo Script (≤ 4 minutes, unedited)

_Last updated: 2026-08-29 (Milestone 4)_

Goal: show a governed multi-agent system catch a broken worker on camera and prove
a human approved the result. Run everything live; do not cut.

## Setup (before recording)
```bash
npm run dev:api     # FastAPI on :8000
npm run dev:web     # dashboard on :5173
```
Open http://localhost:5173. (Optional: set `GOOGLE_API_KEY` in `apps/api/.env` to
route drafting through live Gemini 3.5; the demo also runs fully offline.)

## Beat 1 — the problem (0:00–0:30)
Point at the posture cards: **40 caseloads, 8 overdue, 10 due soon**. "This is one
synthetic district. A special-ed director has no live view of compliance drift
across every caseload — today that's reconstructed during a state audit." Scroll
the caseload table: color-coded annual-review drift, most-urgent first.

## Beat 2 — the multi-agent sweep (0:30–1:30)
Leave the fault selector on **No fault**. Click **Run compliance sweep**. Narrate
the live trace as it streams:
- Timekeeper scans all caseloads → drift alerts.
- Evidence Ingestor normalizes a student's messy notes.
- Document Drafter writes a measurable goal; the supervisor's judge validates it.
- Compliance Reporter rolls up district posture.
Result: **Resolved**, a draft lands in the **Approval gate** as *pending*.

## Beat 3 — break a worker on camera (1:30–2:45) — the signature moment
Set the fault selector to **Hallucination (wrong student / non-measurable)**.
Click **Run compliance sweep** again. In the live trace:
- the Document Drafter returns a goal for the **wrong student** ("Alex Chen"),
- the supervisor's judge **REJECTS** it (wrong student + not measurable),
- the supervisor **kills** the drafter, logs an **incident**, and **reroutes** to a
  healthy fallback,
- the run still ends **Resolved — served by backup_drafter, 1 incident logged**.
Show the **Incident log** entry. (Optional: run **Tool error (transient)** to show
the supervisor *retry the same worker* and recover without a fallback.)

## Beat 4 — prove human sign-off (2:45–3:30)
In the **Approval gate**, read the drafted goal. Keep the approver
("Dr. Alvarez, SpEd Director"). Click **Approve**. It moves to **Decided —
approved by Dr. Alvarez**. "No agent took a binding action; the audit log now proves
a named human signed off." Hit `GET /api/runs/<run_id>/trace` to show the full
due-process trail.

## Beat 5 — the pitch (3:30–4:00)
"Two layers exist — systems of record and per-teacher AI drafters. Neither runs the
district's compliance posture as a live, governed, agentic system, and none can
*prove* a human was in the loop. CaseSentinel does both. Built on Google ADK 2.8 +
Gemini 3.5, deployable to Cloud Run. Synthetic data only."

## Fallbacks
- Rate-limited live Gemini? The offline scripted models reproduce every beat.
- Keep a recorded copy of Beat 3 as insurance (RESEARCH.md flags free-tier RPM).
