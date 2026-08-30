"""Failure injection — a real, testable feature (not a mock).

Builds ADK worker agents that deliberately misbehave so the supervisor's
detect -> kill -> reroute -> log path can be exercised on demand, in tests and
live on camera. Three fault classes:

- ``loop``         : a worker that never terminates (runaway).
- ``hallucination``: a drafter that returns a goal for the wrong student / non-measurable.
- ``tool_error``   : a worker that raises mid-run (a failed tool/service call).

The healthy drafter (``fault="none"``) is the fallback the supervisor reroutes to.
Drafter construction lives in agents/document_drafter.py; this module adds the
looping/crashing workers and the unified ``make_worker`` entry point.
"""

from __future__ import annotations

from typing import AsyncGenerator, Literal

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from pydantic import PrivateAttr

from ..agents.base import Evidence
from ..agents.document_drafter import healthy_goal, make_drafter

FaultType = Literal["none", "loop", "hallucination", "tool_error", "transient_tool_error"]


class LoopingWorker(BaseAgent):
    """Yields work events without ever finishing — a runaway loop."""

    max_yield: int = 1000  # finite safety net; far above any supervisor cap

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        for i in range(self.max_yield):
            yield Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=f"still analyzing... iteration {i}")],
                ),
            )


class CrashingWorker(BaseAgent):
    """Raises mid-run — models a failed tool/service call."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        raise RuntimeError("evidence service timeout (simulated tool failure)")
        yield  # pragma: no cover  (makes this an async generator)


class TransientDrafter(BaseAgent):
    """Crashes on the first attempt, then succeeds — models a transient fault
    that the supervisor's retry-once policy recovers without a fallback."""

    student: str = ""
    _attempts: int = PrivateAttr(default=0)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        self._attempts += 1
        if self._attempts == 1:
            raise RuntimeError("evidence service timeout (transient)")
        yield Event(
            author=self.name,
            content=types.Content(
                role="model", parts=[types.Part(text=healthy_goal(self.student))]
            ),
        )


def make_worker(
    name: str,
    fault: FaultType,
    *,
    student: str,
    evidence: Evidence | None = None,
) -> BaseAgent:
    """Build a worker agent exhibiting the requested fault (or a healthy one)."""
    if fault == "loop":
        return LoopingWorker(name=name)
    if fault == "tool_error":
        return CrashingWorker(name=name)
    if fault == "transient_tool_error":
        return TransientDrafter(name=name, student=student)
    return make_drafter(name, fault, student=student, evidence=evidence)
