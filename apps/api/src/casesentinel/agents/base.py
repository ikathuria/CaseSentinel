"""Shared data shapes for the sub-agents (see docs/02-agent-contracts.md)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DriftAlert:
    student_id: str
    student_name: str
    case_manager_id: str
    deadline_type: str  # annual_review | reevaluation | initial_evaluation | transition_plan
    due_date: str
    days_remaining: int  # negative = overdue
    status: str  # overdue | due_soon | compliant
    severity: str  # high | medium | low

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Evidence:
    student_id: str
    student_name: str
    summary: str
    source_doc_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PostureReport:
    as_of: str
    totals: dict[str, int]
    by_school: dict[str, dict[str, int]]
    by_category: dict[str, dict[str, int]]
    on_time_rate: float  # share of caseloads compliant or due-soon (not overdue)
    at_risk: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
