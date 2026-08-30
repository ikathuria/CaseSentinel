"""Helper to run an ADK agent to a final text string (shared by generative agents)."""

from __future__ import annotations

from contextlib import aclosing

from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

_APP = "casesentinel"


async def run_text(agent: BaseAgent, prompt: str, *, user_id: str = "orchestrator") -> str:
    runner = InMemoryRunner(agent=agent, app_name=_APP)
    session = await runner.session_service.create_session(app_name=_APP, user_id=user_id)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    out = ""
    try:
        async with aclosing(
            runner.run_async(user_id=user_id, session_id=session.id, new_message=message)
        ) as stream:
            async for ev in stream:
                if ev.content and ev.content.parts:
                    for part in ev.content.parts:
                        if getattr(part, "text", None):
                            out = part.text
    finally:
        await runner.close()
    return out
