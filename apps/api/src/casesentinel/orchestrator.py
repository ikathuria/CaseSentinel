"""CaseSentinel orchestrator — runs the four sub-agents sequentially under guard.

Sequential (not parallel) execution is deliberate: it keeps the demo under Gemini
free-tier RPM (RESEARCH.md) and makes the audit trail read as one coherent story.
The whole run shares a single ``run_id``. The high-risk drafter step runs behind
the M0 detect/kill/reroute/log supervisor; every other step is logged too.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from .agents.base import DriftAlert, Evidence, PostureReport
from .agents.compliance_reporter import ComplianceReporter
from .agents.evidence_ingestor import EvidenceIngestor
from .agents.timekeeper import Timekeeper
from .audit.log import AuditLog
from .approval.gate import ApprovalGate
from .guards.failure_injection import FaultType, make_worker
from .guards.supervisor import Supervisor
from .store.base import Store


@dataclass
class PipelineResult:
    run_id: str
    status: str  # resolved | needs_human
    alerts: list[DriftAlert]
    evidence: Evidence
    draft: str | None
    approval: dict[str, Any] | None
    posture: PostureReport
    served_by: str | None
    incidents: list[dict[str, Any]] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "alerts": [a.to_dict() for a in self.alerts],
            "evidence": self.evidence.to_dict(),
            "draft": self.draft,
            "approval": self.approval,
            "posture": self.posture.to_dict(),
            "served_by": self.served_by,
            "incidents": self.incidents,
            "audit_trail": self.audit_trail,
        }


class CaseSentinelOrchestrator:
    def __init__(self, store: Store):
        self._store = store
        self.timekeeper = Timekeeper()
        self.ingestor = EvidenceIngestor()
        self.reporter = ComplianceReporter()
        self.supervisor = Supervisor(store)
        self.gate = ApprovalGate(store)

    async def run_pipeline_async(
        self, district: dict, *, inject_fault: FaultType = "none"
    ) -> PipelineResult:
        audit = AuditLog(self._store)
        audit.record("pipeline_start",
                     detail={"district": district["name"], "inject_fault": inject_fault})

        students = {s["id"]: s for s in district["students"]}

        # 1) Timekeeper — drift across all caseloads.
        alerts = self.timekeeper.scan(district)
        audit.record("agent_complete", agent=self.timekeeper.name,
                     detail={"alerts": len(alerts),
                             "overdue": sum(a.status == "overdue" for a in alerts)})

        # 2) Pick the most-urgent case that has source documents to work from.
        doc_student_ids = {d["student_id"] for d in district["documents"]}
        target = next((a for a in alerts if a.student_id in doc_student_ids),
                      alerts[0] if alerts else None)
        target_student = students[target.student_id] if target else district["students"][0]
        student_name = f"{target_student['first_name']} {target_student['last_name']}"

        # 3) Evidence Ingestor — normalize the messy docs for that student.
        docs = [d for d in district["documents"] if d["student_id"] == target_student["id"]]
        evidence = await self.ingestor.run(target_student, docs)
        audit.record("agent_complete", agent=self.ingestor.name,
                     detail={"student": student_name, "docs": len(evidence.source_doc_ids)})

        # 4) Document Drafter — guarded (fault-injectable), reroutes to fallback on failure.
        primary = make_worker("document_drafter", inject_fault,
                              student=student_name, evidence=evidence)
        fallback = make_worker("backup_drafter", "none",
                               student=student_name, evidence=evidence)
        result = await self.supervisor.supervise_async(
            task_id=f"draft-{target_student['id']}",
            student=student_name,
            prompt=f"Draft one measurable annual reading goal for {student_name}.",
            primary=primary,
            fallback=fallback,
            audit=audit,
        )
        draft = result.output

        # 5) Approval gate — the draft becomes a pending human decision.
        approval = None
        if draft:
            approval = self.gate.create(
                run_id=audit.run_id,
                student_id=target_student["id"],
                student_name=student_name,
                artifact_type="iep_reading_goal",
                content=draft,
                audit=audit,
            )

        # 6) Compliance Reporter — district posture rollup.
        posture = self.reporter.rollup(district, alerts)
        audit.record("agent_complete", agent=self.reporter.name,
                     detail={"on_time_rate": posture.on_time_rate,
                             "overdue": posture.totals["overdue"]})

        audit.record("pipeline_complete", detail={"status": result.status})

        return PipelineResult(
            run_id=audit.run_id,
            status=result.status,
            alerts=alerts,
            evidence=evidence,
            draft=draft,
            approval=approval,
            posture=posture,
            served_by=result.served_by,
            incidents=audit.incidents(),
            audit_trail=audit.entries(),
        )

    def run_pipeline(self, district: dict, *, inject_fault: FaultType = "none") -> PipelineResult:
        return asyncio.run(self.run_pipeline_async(district, inject_fault=inject_fault))
