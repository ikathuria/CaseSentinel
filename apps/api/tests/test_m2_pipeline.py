"""M2 gate: the four agents, the approval gate, and the end-to-end pipeline."""

from __future__ import annotations

import pytest

from casesentinel.agents.compliance_reporter import ComplianceReporter
from casesentinel.agents.evidence_ingestor import EvidenceIngestor
from casesentinel.agents.timekeeper import Timekeeper
from casesentinel.approval.gate import ApprovalError, ApprovalGate
from casesentinel.audit.log import AuditLog
from casesentinel.data.generate import generate_district, to_dict
from casesentinel.guards.judge import judge_goal
from casesentinel.orchestrator import CaseSentinelOrchestrator
from casesentinel.store.local_store import LocalStore

DISTRICT = to_dict(generate_district())


# --- individual agents -------------------------------------------------------

def test_timekeeper_flags_overdue_first():
    alerts = Timekeeper().scan(DISTRICT)
    assert alerts
    assert alerts[0].days_remaining <= 0  # most-urgent first
    assert alerts[0].status == "overdue"
    assert all(a.status in ("overdue", "due_soon") for a in alerts)


def test_evidence_ingestor_normalizes_docs():
    import asyncio
    student = DISTRICT["students"][0]
    docs = [d for d in DISTRICT["documents"] if d["student_id"] == student["id"]]
    evidence = asyncio.run(EvidenceIngestor().run(student, docs))
    assert evidence.student_id == student["id"]
    assert evidence.summary
    assert len(evidence.source_doc_ids) == len(docs)
    # deterministic offline normalizer expands shorthand
    assert "abt" not in evidence.summary.lower() or "about" in evidence.summary.lower()


def test_compliance_reporter_rollup_totals_add_up():
    alerts = Timekeeper().scan(DISTRICT)
    posture = ComplianceReporter().rollup(DISTRICT, alerts)
    assert sum(posture.totals.values()) == len(DISTRICT["students"])
    assert 0.0 <= posture.on_time_rate <= 1.0
    assert posture.totals["overdue"] >= 1


# --- approval gate -----------------------------------------------------------

def test_approval_gate_lifecycle():
    store = LocalStore()
    gate = ApprovalGate(store)
    audit = AuditLog(store, run_id="run-1")
    req = gate.create(run_id="run-1", student_id="stu-001", student_name="Jordan Rivera",
                      artifact_type="iep_reading_goal", content="a goal", audit=audit)
    assert req["status"] == "pending"

    decided = gate.decide(req["id"], approver="Dr. Alvarez (SpEd Director)",
                          decision="approved", audit=audit)
    assert decided["status"] == "approved"
    assert decided["approver"] == "Dr. Alvarez (SpEd Director)"

    # cannot decide twice
    with pytest.raises(ApprovalError):
        gate.decide(req["id"], approver="someone", decision="rejected")

    # the decision is in the audit log with the named approver
    actions = [e["action"] for e in audit.entries()]
    assert "approval_requested" in actions
    assert "approval_decision" in actions


def test_approval_rejects_invalid_decision():
    gate = ApprovalGate(LocalStore())
    req = gate.create(run_id="r", student_id="s", student_name="n",
                      artifact_type="t", content="c")
    with pytest.raises(ApprovalError):
        gate.decide(req["id"], approver="x", decision="maybe")


# --- end-to-end pipeline -----------------------------------------------------

def test_pipeline_happy_path():
    orch = CaseSentinelOrchestrator(LocalStore())
    result = orch.run_pipeline(DISTRICT)
    assert result.status == "resolved"
    assert result.alerts
    assert result.evidence.summary
    assert judge_goal(result.draft, expected_student=result.evidence.student_name).ok
    assert result.approval and result.approval["status"] == "pending"
    assert result.incidents == []
    actions = [e["action"] for e in result.audit_trail]
    for step in ("pipeline_start", "agent_complete", "delegate", "resolved",
                 "approval_requested", "pipeline_complete"):
        assert step in actions, f"missing {step} in {actions}"


@pytest.mark.parametrize("fault", ["loop", "hallucination", "tool_error"])
def test_pipeline_recovers_from_injected_fault(fault):
    orch = CaseSentinelOrchestrator(LocalStore())
    result = orch.run_pipeline(DISTRICT, inject_fault=fault)
    # Recovered end-to-end; a usable draft still reached the approval gate.
    assert result.status == "resolved"
    assert result.served_by == "backup_drafter"
    assert result.approval and result.approval["status"] == "pending"
    assert len(result.incidents) == 1
    assert result.incidents[0]["fault_type"] == fault
    # one shared run_id across the whole trail
    assert {e["run_id"] for e in result.audit_trail} == {result.run_id}
