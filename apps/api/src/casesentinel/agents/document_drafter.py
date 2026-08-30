"""Document Drafter — turns evidence into a measurable IEP goal draft.

Generative and the highest-risk agent, so it is always run behind the supervisor's
guard (see guards/supervisor.py). Production drafting uses gemini-3.5-flash with the
ingested evidence; offline it returns a deterministic healthy goal. The injectable
``hallucination`` fault always uses a scripted wrong-student, non-measurable draft
so the failure demo is reproducible regardless of API key.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from ..models.factory import MODEL_MAIN, has_gemini_key
from ..models.scripted_llm import ScriptedLlm
from .base import Evidence

# A wrong-student, non-measurable goal — fails the judge on two counts.
HALLUCINATED_GOAL = "Alex Chen will get better at reading over time."


def healthy_goal(student: str) -> str:
    first = student.split()[0]
    return (
        f"{first} will read grade-level text at 90 words per minute with 95% "
        f"accuracy in 4 of 5 trials by June 2027."
    )


def make_drafter(
    name: str,
    fault: str = "none",
    *,
    student: str,
    evidence: Evidence | None = None,
) -> LlmAgent:
    """Build the drafter agent (healthy, or a scripted hallucination)."""
    if fault == "hallucination":
        return LlmAgent(
            name=name,
            model=ScriptedLlm(model="scripted", responses=[HALLUCINATED_GOAL]),
            instruction=f"Draft one measurable IEP reading goal for {student}.",
        )

    evidence_text = evidence.summary if evidence else "No evidence provided."
    instruction = (
        f"Draft exactly one measurable annual IEP reading goal for {student}. "
        f"Reference the student by name, include a numeric criterion (e.g. words per "
        f"minute and accuracy %), and base it on this evidence:\n{evidence_text}"
    )
    if has_gemini_key():
        return LlmAgent(name=name, model=MODEL_MAIN, instruction=instruction)
    return LlmAgent(
        name=name,
        model=ScriptedLlm(model="scripted", responses=[healthy_goal(student)]),
        instruction=instruction,
    )
