"""Heuristic output judge for drafted IEP goals.

Catches the two failure modes the competitor research flagged as unserved
(RESEARCH.md): a goal written for the *wrong student* (the real "copy-and-paste
another kid's name" defect) and a *non-measurable* goal ("A goal can pass every
required-field check and still be unmeasurable").

Detection is intentionally robust against real LLM prose: it checks that the goal
names the expected student and states a numeric criterion, rather than trying to
recognize arbitrary names (which false-positives on capitalized phrases like
"Reading Goal"). A goal about a different student fails the "names the expected
student" check; M3 can add a second-model judge behind the same signature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# A goal is "measurable" if it states a numeric criterion in any common form.
_MEASURABLE = re.compile(
    r"(\d+\s?%"
    r"|\bpercent\b|\baccuracy\b"
    r"|\b\d+\s?(?:wpm|wcpm|words|word|minute|minutes|problems|trials|times|questions|sentences)\b"
    r"|\b\d+\s*(?:of|out of|/)\s*\d+\b"
    r"|\bby\s+\w+\s+\d{4}\b)",
    re.IGNORECASE,
)


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
        # A goal that doesn't name the expected student is either generic
        # boilerplate or written for someone else — both unacceptable.
        reasons.append(f"does not mention the student ({expected_student})")

    if not _MEASURABLE.search(body):
        reasons.append("goal is not measurable (no numeric criterion)")

    return Verdict(ok=not reasons, reasons=reasons)
