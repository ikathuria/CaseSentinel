"""Content-validation guards (detection mechanism #2: hallucination).

A judge is a callable ``(text) -> (ok, reason)``. The supervisor runs one after a
worker finishes to catch output that executed cleanly but is wrong — a goal for the
wrong student, a non-measurable goal, or empty output. Kept separate from the
execution guard (loop_guard.py) so detection concerns don't bleed together.
"""

from __future__ import annotations

from typing import Callable

from .judge import judge_goal

Judge = Callable[[str], tuple[bool, "str | None"]]


def goal_judge(student: str) -> Judge:
    """Judge drafted IEP goals for a specific student."""

    def _judge(text: str) -> tuple[bool, str | None]:
        verdict = judge_goal(text or "", expected_student=student)
        return verdict.ok, ("; ".join(verdict.reasons) or None)

    return _judge


def nonempty_judge(text: str) -> tuple[bool, str | None]:
    """Generic validator for non-drafter agents: output must be non-empty."""
    ok = bool(text and text.strip())
    return ok, (None if ok else "empty output")
