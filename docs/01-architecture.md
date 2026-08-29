# 01 — Architecture

_Last updated: 2026-08-29 (Milestone 0 complete)_

CaseSentinel is a supervisor/orchestrator agent that delegates to specialized
sub-agents, monitors them, and recovers from their failures — writing every
consequential step to an append-only audit log. This document records the
**proven** M0 mechanism; later milestones build on it unchanged.

## The failure-recovery loop (proven in M0)

```
                       ┌─────────────────────────────────────────────┐
                       │                SUPERVISOR                    │
                       │  (casesentinel.guards.supervisor.Supervisor) │
                       └─────────────────────────────────────────────┘
        delegate │                      ▲  detect (guard)      │ log every step
                 ▼                      │                      ▼
        ┌──────────────────┐   kill    │              ┌───────────────────┐
        │  primary worker  │──fault────┘              │  append-only audit │
        │  (ADK LlmAgent / │                          │  + incident record │
        │   BaseAgent)     │                          │ (audit.log.AuditLog)│
        └──────────────────┘                          └───────────────────┘
                 │ reroute (supervisor-side dispatch, NOT transfer_to_agent)
                 ▼
        ┌──────────────────┐   judge ok → RESOLVED
        │ fallback worker  │───────────────────────────────► output returned
        └──────────────────┘   judge fails / faults again → NEEDS_HUMAN (escalate)
```

### Detection — three fault classes, three mechanisms
Each worker runs inside `Supervisor._run_guarded`, which wraps ADK's
`Runner.run_async` event stream:

| Fault class | How it's injected (real, testable) | How the supervisor detects it |
|---|---|---|
| **loop** (runaway) | `LoopingWorker` yields work events without terminating | event count exceeds `max_iterations` → generator is `aclose()`d (killed) |
| **tool_error** (crash) | `CrashingWorker` raises mid-run | exception caught around the stream |
| **hallucination** (bad content) | scripted `LlmAgent` returns a wrong-student, non-measurable goal | `guards.judge.judge_goal` heuristic rejects the final output |
| _(also)_ **model_error** | model returns an error event | `event.error_code` / `error_message` set |

### Recovery — supervisor-side, deliberately not `transfer_to_agent`
On any detected fault the supervisor: (1) records a `kill` audit entry, (2) writes
a structured **incident**, (3) records a `reroute`, and (4) dispatches the same task
to a healthy **fallback** worker. If the fallback also faults or its output fails
the judge, the supervisor writes a second incident and **escalates to a human**
(`needs_human`) — never taking a binding action itself. Recovery is done in the
supervisor's own control loop because `transfer_to_agent` back to a parent is
reported broken for sub-agents (adk-python #4110) — see PLAN.md decision log.

### Audit — the due-process paper trail
`AuditLog` (scoped per run via `run_id`) appends immutable records to the `Store`
for every action: `delegate`, `judge`, `kill`, `incident`, `reroute`, `resolved`,
`escalate_to_human`. Incidents are also mirrored into their own collection. The
`LocalStore` (JSONL / in-memory) backs tests and the offline demo; a Firestore
store swaps in for deploy behind the same `Store` interface.

## Key ADK 2.8 primitives used (verified 2026-08-29 against installed 2.8.0)
- `google.adk.agents.LlmAgent` — workers; supports `before/after_model_callback`,
  `on_model_error_callback`, `on_tool_error_callback`, `retry_config`, `timeout`
  (2.8 additions the guards will lean on further in M3).
- `google.adk.agents.BaseAgent._run_async_impl` — custom workers (looping/crashing).
- `google.adk.runners.InMemoryRunner` / `Runner.run_async` — the execution stream.
- `google.adk.models.BaseLlm` — subclassed as `ScriptedLlm` for offline, rate-limit-free runs.
- `google.adk.events.EventActions.escalate` — available for in-agent escalation (M3).

## Offline-first model layer
`models.factory.get_model` returns a live Gemini model (`gemini-3.5-flash` /
`-flash-lite`) when `GOOGLE_API_KEY` is set, and a deterministic `ScriptedLlm`
otherwise. This makes the entire failure-recovery path testable with no key and
lets the live demo run with **zero rate-limit risk** — the single biggest
live-demo hazard flagged in RESEARCH.md.

## Run it
```bash
# offline demo of all four scenarios
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m casesentinel.spike.run_spike

# test gate
cd apps/api && .venv/bin/python -m pytest -q

# optional: live Gemini smoke (needs a key)
GOOGLE_API_KEY=... apps/api/.venv/bin/python -m casesentinel.spike.smoke_gemini
```
