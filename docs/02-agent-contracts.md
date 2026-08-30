# 02 — Agent Contracts

_Last updated: 2026-08-29 (Milestone 2)_

Strict separation of concerns is a scored rubric item. Every agent has one job, a
typed input, a typed output, and a defined failure mode. The **supervisor**
(orchestrator) delegates to them **sequentially** (RPM-safe) and writes every step
to the audit log. No agent takes a binding action — consequential output is routed
to a human via the approval gate.

| Agent | Kind | Input | Output | Model | Failure mode → handling |
|---|---|---|---|---|---|
| **Timekeeper** | analytic (deterministic) | district cases + `as_of` | `DriftAlert[]` (sorted, most-urgent first) | none | pure computation; can't hallucinate |
| **Evidence Ingestor** | generative | a student's messy source docs | `Evidence` (normalized summary + source ids) | `gemini-3.5-flash-lite` / scripted | empty/garbled → drafter still guarded downstream |
| **Document Drafter** | generative | student + `Evidence` | draft goal (PLAAFP/goal/PWN/BIP) | `gemini-3.5-flash` / scripted | loop / hallucination / tool_error → supervisor kills, reroutes to fallback, logs incident |
| **Compliance Reporter** | analytic (deterministic) | district + `DriftAlert[]` | `PostureReport` (district rollup vs. state indicators) | none | pure computation |

## The orchestration (M2 pipeline)

```
Orchestrator.run_pipeline(district, inject_fault=None)
  │  audit: pipeline_start
  ├─ Timekeeper.scan ............... DriftAlert[]         audit: agent_complete[timekeeper]
  ├─ pick most-urgent case
  ├─ EvidenceIngestor.run .......... Evidence            audit: agent_complete[evidence_ingestor]
  ├─ Supervisor.supervise(Drafter) . draft (guarded)     audit: delegate/judge/kill/reroute/resolved (+incident)
  ├─ ApprovalGate.create ........... ApprovalRequest      audit: approval_requested   (status = pending)
  ├─ ComplianceReporter.rollup ..... PostureReport        audit: agent_complete[compliance_reporter]
  │  audit: pipeline_complete
  └─ PipelineResult{alerts, evidence, draft, approval_request, posture, incidents, run_id}
```

The whole pipeline shares **one** `run_id`, so the audit trail reads as a single
coherent story (the due-process record for that run). The guarded drafter step
reuses the M0 detect/kill/reroute/log core (`guards/supervisor.py`).

## Approval gate (first-class object)

`ApprovalRequest`: `{id, run_id, student, artifact_type, content, status, approver, reason, timestamps}`.
Lifecycle: **pending → approved | rejected**. State is derived from append-only
records (creation + immutable decision events) so the store stays append-only and
the audit trail is tamper-evident. `decide(approver, decision)` is the only way a
draft becomes actionable — enforcing human sign-off as a feature, not an afterthought.

## Data shapes (see `agents/base.py`)
- `DriftAlert{student_id, student_name, case_manager_id, deadline_type, due_date, days_remaining, status, severity}`
- `Evidence{student_id, student_name, summary, source_doc_ids}`
- `PostureReport{as_of, totals{overdue,due_soon,compliant}, by_school, by_category, on_time_rate, at_risk[]}`
