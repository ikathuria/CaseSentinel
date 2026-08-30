"""The supervisor: delegate, monitor, detect failure, recover, and log.

CaseSentinel's failure-tolerant orchestration core and the subject of the signature
demo. It runs a worker under guard (loop_guard + a content judge); on failure it
applies a recovery policy and logs a structured incident:

  * transient fault (tool_error / model_error) -> retry the SAME worker once
  * systematic fault (loop / hallucination)     -> reroute immediately to a fallback
  * fallback also fails                          -> escalate to a human (needs_human)

No agent takes a binding action. Recovery is supervisor-side (catch/dispatch), NOT
``transfer_to_agent`` back to a parent, which is reported broken for sub-agents in
ADK (adk-python #4110) — see PLAN.md decision log.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from google.adk.agents import BaseAgent

from ..audit.log import AuditLog
from ..store.base import Store
from .callbacks import Judge, goal_judge, nonempty_judge
from .loop_guard import DEFAULT_MAX_ITERATIONS, GuardOutcome, run_guarded

TRANSIENT_FAULTS = {"tool_error", "model_error"}


@dataclass
class SuperviseResult:
    task_id: str
    status: str  # "resolved" | "needs_human"
    output: str | None
    served_by: str | None
    run_id: str
    action_taken: str | None = None  # retried_recovered | reroute_to_fallback | escalate_to_human
    incidents: list[dict[str, Any]] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)


class Supervisor:
    def __init__(self, store: Store):
        self._store = store

    async def _evaluate(
        self, agent: BaseAgent, prompt: str, judge: Judge, *, max_iterations: int
    ) -> tuple[GuardOutcome, str | None]:
        """Run under guard, then judge content. Returns (outcome, fault)."""
        outcome = await run_guarded(agent, prompt, max_iterations=max_iterations)
        if outcome.fault:
            return outcome, outcome.fault
        ok, reason = judge(outcome.output or "")
        if not ok:
            outcome.detection = reason
            return outcome, "hallucination"
        return outcome, None

    async def supervise_async(
        self,
        *,
        task_id: str,
        student: str,
        prompt: str,
        primary: BaseAgent,
        fallback: BaseAgent,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        judge: Judge | None = None,
        audit: AuditLog | None = None,
    ) -> SuperviseResult:
        audit = audit or AuditLog(self._store)
        judge = judge or (goal_judge(student) if student else nonempty_judge)
        audit.record("delegate", agent=primary.name, detail={"task_id": task_id, "student": student})

        outcome, fault = await self._evaluate(primary, prompt, judge, max_iterations=max_iterations)
        audit.record("judge", agent=primary.name,
                     detail={"ok": fault is None, "fault": fault, "detection": outcome.detection})

        if fault is None:
            audit.record("resolved", agent=primary.name, detail={"served_by": primary.name})
            return self._result(task_id, "resolved", outcome.output, primary.name, None, audit)

        # --- failure path -----------------------------------------------------
        detection = outcome.detection
        audit.record("kill", agent=primary.name, detail={"fault": fault, "detection": detection})

        served_by: str | None = None
        final_output: str | None = None
        action: str | None = None

        # 1) retry once for transient faults (same worker instance).
        if fault in TRANSIENT_FAULTS:
            audit.record("retry", agent=primary.name, detail={"attempt": 2})
            retry_outcome, retry_fault = await self._evaluate(
                primary, prompt, judge, max_iterations=max_iterations
            )
            if retry_fault is None:
                action, served_by, final_output = "retried_recovered", primary.name, retry_outcome.output
            else:
                audit.record("kill", agent=primary.name,
                             detail={"fault": retry_fault, "detection": retry_outcome.detection, "attempt": 2})

        # 2) reroute to the fallback worker.
        if action is None:
            audit.record("reroute", agent=fallback.name, detail={"from": primary.name})
            fb_outcome, fb_fault = await self._evaluate(
                fallback, prompt, judge, max_iterations=max_iterations
            )
            if fb_fault is None:
                action, served_by, final_output = "reroute_to_fallback", fallback.name, fb_outcome.output
            else:
                action = "escalate_to_human"

        # One incident per fault episode; action_taken captures the outcome.
        audit.record_incident(
            agent=primary.name,
            fault_type=fault,
            detection=detection or "",
            action_taken=action,
            detail={"task_id": task_id},
        )

        if action == "escalate_to_human":
            audit.record("escalate_to_human", detail={"task_id": task_id})
            return self._result(task_id, "needs_human", None, None, action, audit)

        audit.record("resolved", agent=served_by, detail={"served_by": served_by})
        return self._result(task_id, "resolved", final_output, served_by, action, audit)

    def supervise(self, **kwargs: Any) -> SuperviseResult:
        return asyncio.run(self.supervise_async(**kwargs))

    def _result(self, task_id, status, output, served_by, action, audit: AuditLog) -> SuperviseResult:
        return SuperviseResult(
            task_id=task_id,
            status=status,
            output=output,
            served_by=served_by,
            run_id=audit.run_id,
            action_taken=action,
            incidents=audit.incidents(),
            audit_trail=audit.entries(),
        )
