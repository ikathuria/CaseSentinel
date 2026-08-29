"""A deterministic, offline LLM for tests and rate-limit-free demos.

`ScriptedLlm` is a real `google.adk.models.BaseLlm` implementation that returns
canned responses instead of calling Gemini. It lets the whole failure-detection /
recovery pipeline run and be unit-tested with **no API key and no rate limits**,
while the agents, Runner, and callbacks remain exactly the real ADK primitives.

Swap it for a real Gemini model via `casesentinel.models.factory.get_model`.
"""

from __future__ import annotations

from typing import AsyncGenerator

from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types
from pydantic import PrivateAttr


class ScriptedLlm(BaseLlm):
    """Yields pre-scripted responses in order; repeats the last one if exhausted.

    Args:
        model: a label (unused for routing; kept for parity with real models).
        responses: the text responses to yield, one per model call.
    """

    responses: list[str] = []
    _idx: int = PrivateAttr(default=0)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        if not self.responses:
            text = ""
        else:
            text = self.responses[min(self._idx, len(self.responses) - 1)]
        self._idx += 1
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=text)])
        )
