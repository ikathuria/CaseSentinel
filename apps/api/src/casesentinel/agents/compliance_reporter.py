"""Compliance Reporter — rolls caseload status into a district posture report.

Deterministic aggregation against state-indicator-style metrics (on-time rate,
overdue counts by school and disability category, the at-risk list a director acts
on). This is the district-scoped view no per-teacher competitor produces.
"""

from __future__ import annotations

from .base import DriftAlert, PostureReport

_EMPTY = {"overdue": 0, "due_soon": 0, "compliant": 0}


def _worst(a: str, b: str) -> str:
    order = {"overdue": 2, "due_soon": 1, "compliant": 0}
    return a if order[a] >= order[b] else b


class ComplianceReporter:
    name = "compliance_reporter"

    def rollup(self, district: dict, alerts: list[DriftAlert]) -> PostureReport:
        students = {s["id"]: s for s in district["students"]}
        schools = {s["id"]: s["name"] for s in district["schools"]}

        # Worst status per student across all their deadlines.
        worst: dict[str, str] = {sid: "compliant" for sid in students}
        for a in alerts:
            worst[a.student_id] = _worst(worst[a.student_id], a.status)

        totals = dict(_EMPTY)
        by_school: dict[str, dict[str, int]] = {}
        by_category: dict[str, dict[str, int]] = {}

        for sid, status in worst.items():
            student = students[sid]
            totals[status] += 1
            school = schools.get(student["school_id"], student["school_id"])
            cat = student["disability_category"]
            by_school.setdefault(school, dict(_EMPTY))[status] += 1
            by_category.setdefault(cat, dict(_EMPTY))[status] += 1

        total = max(sum(totals.values()), 1)
        on_time_rate = round((total - totals["overdue"]) / total, 3)

        at_risk = [
            {
                "student_id": a.student_id,
                "student_name": a.student_name,
                "deadline_type": a.deadline_type,
                "due_date": a.due_date,
                "days_remaining": a.days_remaining,
                "status": a.status,
                "severity": a.severity,
            }
            for a in alerts
            if a.status == "overdue"
        ][:10]

        return PostureReport(
            as_of=district["as_of"],
            totals=totals,
            by_school=by_school,
            by_category=by_category,
            on_time_rate=on_time_rate,
            at_risk=at_risk,
        )
