"""Model factory: real Gemini when a key is present, scripted model otherwise.

Keeping model selection behind one function means the agents, supervisor, and
tests are identical whether they run against `gemini-3.5-flash` or the offline
`ScriptedLlm`. It also means the live demo can run with zero rate-limit risk
(PLAN.md decision).
"""

from __future__ import annotations

import os

from google.adk.models import BaseLlm

from .scripted_llm import ScriptedLlm

MODEL_MAIN = os.environ.get("GEMINI_MODEL_MAIN", "gemini-3.5-flash")
MODEL_LITE = os.environ.get("GEMINI_MODEL_LITE", "gemini-3.5-flash-lite")


def has_gemini_key() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def get_model(role: str = "main", *, scripted: list[str] | None = None) -> BaseLlm | str:
    """Return a model for the given role.

    If ``scripted`` responses are supplied and no key is set, return a
    ``ScriptedLlm``; otherwise return the Gemini model-name string that ADK
    resolves to a live model. Passing ``scripted`` always wins when offline so
    tests are deterministic.
    """
    if scripted is not None and not has_gemini_key():
        return ScriptedLlm(model="scripted", responses=scripted)
    return MODEL_LITE if role == "lite" else MODEL_MAIN
