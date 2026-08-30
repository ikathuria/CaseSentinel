"""Loop / execution guard — runs one agent under an iteration cap and catches crashes.

Detection mechanism #1 (runaway loops) and #3 (tool/worker crashes). Content
validation (#2, hallucination) lives in guards/callbacks.py. Agent-agnostic: works
on any ADK ``BaseAgent`` (LlmAgent or custom), so the supervisor can monitor every
sub-agent with the same code.
"""

from __future__ import annotations

from contextlib import aclosing
from dataclasses import dataclass

from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

_APP = "casesentinel"
DEFAULT_MAX_ITERATIONS = 5


@dataclass
class GuardOutcome:
    output: str | None
    fault: str | None  # None | "loop" | "tool_error" | "model_error"
    detection: str | None
    events: int


async def run_guarded(
    agent: BaseAgent, prompt: str, *, max_iterations: int = DEFAULT_MAX_ITERATIONS
) -> GuardOutcome:
    """Run ``agent`` on ``prompt``, killing it if it loops or crashes."""
    runner = InMemoryRunner(agent=agent, app_name=_APP)
    session = await runner.session_service.create_session(app_name=_APP, user_id="supervisor")
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    output: str | None = None
    count = 0
    result: GuardOutcome | None = None
    # aclosing() finalizes the worker's async generator in-context on early kill,
    # avoiding OpenTelemetry context leaks.
    try:
        async with aclosing(
            runner.run_async(user_id="supervisor", session_id=session.id, new_message=message)
        ) as stream:
            async for ev in stream:
                count += 1
                if ev.error_code or ev.error_message:
                    result = GuardOutcome(None, "model_error", ev.error_message or ev.error_code, count)
                    break
                if count > max_iterations:
                    result = GuardOutcome(None, "loop", f"exceeded cap of {max_iterations} steps", count)
                    break
                if ev.content and ev.content.parts:
                    for part in ev.content.parts:
                        if getattr(part, "text", None):
                            output = part.text
    except Exception as exc:  # worker/tool crash
        result = GuardOutcome(None, "tool_error", f"{type(exc).__name__}: {exc}", count)
    finally:
        await runner.close()
    return result or GuardOutcome(output, None, None, count)
