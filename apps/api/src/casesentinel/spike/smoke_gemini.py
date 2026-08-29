"""Live Gemini smoke test — proves a minimal LlmAgent reaches gemini-3.5-flash.

    GOOGLE_API_KEY=... python -m casesentinel.spike.smoke_gemini

Prints the model's response, or a clear message if no API key is configured.
The rest of M0 runs fully offline; this is the one path that needs a key.
"""

from __future__ import annotations

import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from ..models.factory import MODEL_MAIN, has_gemini_key


async def _run() -> str | None:
    agent = LlmAgent(
        name="smoke",
        model=MODEL_MAIN,
        instruction="Reply with exactly one short sentence.",
    )
    runner = InMemoryRunner(agent=agent, app_name="smoke")
    session = await runner.session_service.create_session(app_name="smoke", user_id="u")
    text = None
    try:
        async for ev in runner.run_async(
            user_id="u",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text="Say hello from CaseSentinel in one sentence.")],
            ),
        ):
            if ev.content and ev.content.parts:
                for p in ev.content.parts:
                    if getattr(p, "text", None):
                        text = p.text
    finally:
        await runner.close()
    return text


def main() -> None:
    if not has_gemini_key():
        print("No GOOGLE_API_KEY / GEMINI_API_KEY set — skipping live Gemini call.")
        print("Add your key to apps/api/.env to run this smoke test.")
        return
    print(f"Calling {MODEL_MAIN} ...")
    print("Gemini says:", _run_sync())


def _run_sync() -> str | None:
    return asyncio.run(_run())


if __name__ == "__main__":
    main()
