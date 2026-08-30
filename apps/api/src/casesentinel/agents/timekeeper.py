"""Timekeeper — watches deadlines across every caseload and raises drift.

Deterministic by design: deadline math must never hallucinate. Computes days to
each mandated deadline relative to the district's ``as_of`` date and emits a
``DriftAlert`` for anything overdue or due soon, most-urgent first. This is the
continuous-monitoring differentiator (RESEARCH.md): no competitor surfaces
district-wide drift proactively.
"""

from __future__ import annotations

from datetime import date

from .base import DriftAlert

DUE_SOON_WINDOW_DAYS = 30

_DEADLINE_FIELDS = {
    "annual_review": "annual_review_due",
    "reevaluation": "reevaluation_due",
    "initial_evaluation": "initial_evaluation_due",
    "transition_plan": "transition_plan_due",
}


def _classify(days: int) -> tuple[str, str]:
    if days < 0:
        return "overdue", "high"
    if days <= DUE_SOON_WINDOW_DAYS:
        return "due_soon", "medium"
    return "compliant", "low"


class Timekeeper:
    name = "timekeeper"

    def scan(self, district: dict, *, include_compliant: bool = False) -> list[DriftAlert]:
        as_of = date.fromisoformat(district["as_of"])
        students = {s["id"]: s for s in district["students"]}
        alerts: list[DriftAlert] = []

        for case in district["cases"]:
            student = students.get(case["student_id"])
            if not student:
                continue
            for deadline_type, field_name in _DEADLINE_FIELDS.items():
                due_raw = case.get(field_name)
                if not due_raw:
                    continue
                days = (date.fromisoformat(due_raw) - as_of).days
                status, severity = _classify(days)
                if status == "compliant" and not include_compliant:
                    continue
                alerts.append(
                    DriftAlert(
                        student_id=student["id"],
                        student_name=f"{student['first_name']} {student['last_name']}",
                        case_manager_id=student["case_manager_id"],
                        deadline_type=deadline_type,
                        due_date=due_raw,
                        days_remaining=days,
                        status=status,
                        severity=severity,
                    )
                )

        # Most urgent first (most overdue -> soonest due).
        alerts.sort(key=lambda a: a.days_remaining)
        return alerts
