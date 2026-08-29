"""Heuristic output judge for drafted IEP goals.

Catches the two most common failure modes of an LLM drafter that the competitor
research flagged as unserved (RESEARCH.md): a goal written for the *wrong student*
(the real "copy-and-paste another kid's name" defect) and a *non-measurable* goal
("A goal can pass every required-field check and still be unmeasurable").

M0 uses cheap heuristics; M3 can add a second-model judge behind the same
``judge_goal`` signature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Signals that a goal is measurable: a number, percent, ratio, or an explicit criterion word.
_MEASURABLE = re.compile(
    r"(\d+\s?%|\b\d+\s?(?:wpm|words|problems|trials|out of|/)\b|\bpercent\b|\baccuracy\b|\bby\s+\d)",
    re.IGNORECASE,
)
# Rough proper-name detector (Titlecase word pairs), used to spot a foreign student name.
_NAME = re.compile(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b")


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def judge_goal(text: str, *, expected_student: str) -> Verdict:
    """Return whether ``text`` is an acceptable goal for ``expected_student``."""
    reasons: list[str] = []
    body = (text or "").strip()

    if not body:
        return Verdict(ok=False, reasons=["empty output"])

    first_name = expected_student.split()[0].lower()
    if first_name not in body.lower():
        reasons.append(f"does not mention the student ({expected_student})")

    # A full name that is not the expected student => likely another student's data.
    for a, b in _NAME.findall(body):
        full = f"{a} {b}"
        if full.lower() != expected_student.lower() and a.lower() != first_name:
            reasons.append(f"references a different student's name ({full})")
            break

    if not _MEASURABLE.search(body):
        reasons.append("goal is not measurable (no numeric criterion)")

    return Verdict(ok=not reasons, reasons=reasons)
