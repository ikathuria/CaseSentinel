"""The supervisor: delegate, monitor, detect failure, kill, reroute, and log.

This is CaseSentinel's failure-tolerant orchestration core and the subject of the
signature demo. It runs a worker agent under guard; if the worker loops, crashes,
or returns a hallucinated/unusable draft, the supervisor stops it, records an
incident, and reroutes to a healthy fallback — escalating to a human only when the
fallback also fails. Every step is written to the append-only audit log.

Recovery is done supervisor-side (catch/dispatch), deliberately NOT via
``transfer_to_agent`` back to a parent, which is reported broken for sub-agents in
ADK (adk-python #4110) — see PLAN.md decision log.
"""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from dataclasses import dataclass, field
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from ..audit.log import AuditLog
from ..store.base import Store
from .judge import judge_goal

_APP = "casesentinel"


@dataclass
class GuardedRun:
    output: str | None
    fault: str | None  # None | "loop" | "tool_error" | "model_error"
    detection: str | None
    events: int


@dataclass
class SuperviseResult:
    task_id: str
    status: str  # "resolved" | "needs_human"
    output: str | None
    served_by: str | None
    run_id: str
    incidents: list[dict[str, Any]] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)


class Supervisor:
    def __init__(self, store: Store):
        self._store = store

    async def _run_guarded(
        self, agent: BaseAgent, prompt: str, *, max_iterations: int
    ) -> GuardedRun:
        """Run one worker, enforcing an iteration cap and catching crashes."""
        runner = InMemoryRunner(agent=agent, app_name=_APP)
        session = await runner.session_service.create_session(
            app_name=_APP, user_id="supervisor"
        )
        output: str | None = None
        count = 0
        result: GuardedRun | None = None
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        # aclosing() guarantees the worker's async generator is finalized inside
        # this task's context when we kill it early, avoiding OTel context leaks.
        try:
            async with aclosing(
                runner.run_async(
                    user_id="supervisor", session_id=session.id, new_message=message
                )
            ) as stream:
                async for ev in stream:
                    count += 1
                    if ev.error_code or ev.error_message:
                        result = GuardedRun(None, "model_error", ev.error_message or ev.error_code, count)
                        break
                    if count > max_iterations:
                        # Kill: stop consuming the runaway worker's output.
                        result = GuardedRun(None, "loop", f"exceeded cap of {max_iterations} steps", count)
                        break
                    if ev.content and ev.content.parts:
                        for part in ev.content.parts:
                            if getattr(part, "text", None):
                                output = part.text
        except Exception as exc:  # worker/tool crash
            result = GuardedRun(None, "tool_error", f"{type(exc).__name__}: {exc}", count)
        finally:
            await runner.close()
        return result or GuardedRun(output, None, None, count)

    async def supervise_async(
        self,
        *,
        task_id: str,
        student: str,
        prompt: str,
        primary: BaseAgent,
        fallback: BaseAgent,
        max_iterations: int = 5,
    ) -> SuperviseResult:
        audit = AuditLog(self._store)
        audit.record("delegate", agent=primary.name, detail={"task_id": task_id, "student": student})

        run = await self._run_guarded(primary, prompt, max_iterations=max_iterations)
        fault, detection, output = run.fault, run.detection, run.output

        # No execution fault? Still gate the content through the judge.
        if fault is None:
            verdict = judge_goal(output or "", expected_student=student)
            audit.record(
                "judge",
                agent=primary.name,
                detail={"ok": verdict.ok, "reasons": verdict.reasons},
            )
            if not verdict.ok:
                fault, detection = "hallucination", "; ".join(verdict.reasons)

        if fault is None:
            audit.record("resolved", agent=primary.name, detail={"served_by": primary.name})
            return self._result(task_id, "resolved", output, primary.name, audit)

        # Failure path: kill -> incident -> reroute.
        audit.record("kill", agent=primary.name, detail={"fault": fault, "detection": detection})
        audit.record_incident(
            agent=primary.name,
            fault_type=fault,
            detection=detection or "",
            action_taken="reroute_to_fallback",
            detail={"task_id": task_id},
        )
        audit.record("reroute", agent=fallback.name, detail={"from": primary.name})

        fb = await self._run_guarded(fallback, prompt, max_iterations=max_iterations)
        if fb.fault is None:
            fb_verdict = judge_goal(fb.output or "", expected_student=student)
            audit.record(
                "judge",
                agent=fallback.name,
                detail={"ok": fb_verdict.ok, "reasons": fb_verdict.reasons},
            )
            if fb_verdict.ok:
                audit.record("resolved", agent=fallback.name, detail={"served_by": fallback.name})
                return self._result(task_id, "resolved", fb.output, fallback.name, audit)

        # Fallback also failed -> escalate to a human (no binding action taken).
        audit.record_incident(
            agent=fallback.name,
            fault_type=fb.fault or "hallucination",
            detection=fb.detection or "fallback output rejected by judge",
            action_taken="escalate_to_human",
            detail={"task_id": task_id},
        )
        audit.record("escalate_to_human", detail={"task_id": task_id})
        return self._result(task_id, "needs_human", None, None, audit)

    def supervise(self, **kwargs: Any) -> SuperviseResult:
        """Synchronous entry point."""
        return asyncio.run(self.supervise_async(**kwargs))

    def _result(
        self, task_id: str, status: str, output: str | None, served_by: str | None, audit: AuditLog
    ) -> SuperviseResult:
        return SuperviseResult(
            task_id=task_id,
            status=status,
            output=output,
            served_by=served_by,
            run_id=audit.run_id,
            incidents=audit.incidents(),
            audit_trail=audit.entries(),
        )
