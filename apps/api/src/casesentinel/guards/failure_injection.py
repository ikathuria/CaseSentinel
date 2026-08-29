"""Failure injection — a real, testable feature (not a mock).

Builds ADK worker agents that deliberately misbehave so the supervisor's
detect -> kill -> reroute -> log path can be exercised on demand, in tests and
live on camera. Three fault classes:

- ``loop``        : a worker that never terminates (runaway).
- ``hallucination``: a drafter that returns a goal for the wrong student / non-measurable.
- ``tool_error``  : a worker that raises mid-run (a failed tool/service call).

The healthy drafter (``fault="none"``) is the fallback the supervisor reroutes to.
All drafters use the scripted model so injected behavior is deterministic and
runs offline; production drafting uses a live Gemini model (see models.factory).
"""

from __future__ import annotations

from typing import AsyncGenerator, Literal

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from ..models.scripted_llm import ScriptedLlm

FaultType = Literal["none", "loop", "hallucination", "tool_error"]

# A wrong-student, non-measurable goal — fails the judge on two counts.
_HALLUCINATED_GOAL = "Alex Chen will get better at reading over time."


def _healthy_goal(student: str) -> str:
    first = student.split()[0]
    return (
        f"{first} will read grade-level text at 90 words per minute with 95% "
        f"accuracy in 4 of 5 trials by June 2027."
    )


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


def make_worker(name: str, fault: FaultType, *, student: str) -> BaseAgent:
    """Build a worker agent exhibiting the requested fault (or a healthy one)."""
    if fault == "loop":
        return LoopingWorker(name=name)
    if fault == "tool_error":
        return CrashingWorker(name=name)

    response = _HALLUCINATED_GOAL if fault == "hallucination" else _healthy_goal(student)
    return LlmAgent(
        name=name,
        model=ScriptedLlm(model="scripted", responses=[response]),
        instruction=f"Draft one measurable IEP reading goal for {student}.",
    )
