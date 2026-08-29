"""M0 gate: injecting each fault must yield detection + recovery + an audit record."""

from __future__ import annotations

import pytest

from casesentinel.guards.failure_injection import make_worker
from casesentinel.guards.judge import judge_goal
from casesentinel.guards.supervisor import Supervisor
from casesentinel.store.local_store import LocalStore

STUDENT = "Jordan Rivera"
PROMPT = f"Draft one measurable annual reading goal for {STUDENT}."


def _supervise(fault: str):
    supervisor = Supervisor(LocalStore())
    return supervisor.supervise(
        task_id=f"draft-{fault}",
        student=STUDENT,
        prompt=PROMPT,
        primary=make_worker("document_drafter", fault, student=STUDENT),
        fallback=make_worker("backup_drafter", "none", student=STUDENT),
        max_iterations=5,
    )


def test_healthy_run_resolves_without_incident():
    result = _supervise("none")
    assert result.status == "resolved"
    assert result.served_by == "document_drafter"
    assert result.incidents == []
    assert judge_goal(result.output, expected_student=STUDENT).ok


@pytest.mark.parametrize("fault", ["loop", "hallucination", "tool_error"])
def test_injected_fault_is_detected_recovered_and_logged(fault):
    result = _supervise(fault)

    # Recovered: rerouted to the healthy fallback, producing a valid goal.
    assert result.status == "resolved", f"{fault} did not recover: {result}"
    assert result.served_by == "backup_drafter"
    assert judge_goal(result.output, expected_student=STUDENT).ok

    # Detected + logged: exactly the injected fault, with a reroute action.
    assert len(result.incidents) == 1
    incident = result.incidents[0]
    assert incident["fault_type"] == fault
    assert incident["agent"] == "document_drafter"
    assert incident["action_taken"] == "reroute_to_fallback"
    assert incident["detection"]

    # Audit trail tells the whole story in order.
    actions = [e["action"] for e in result.audit_trail]
    assert actions[0] == "delegate"
    for step in ("kill", "incident", "reroute", "resolved"):
        assert step in actions, f"missing '{step}' in {actions}"


def test_judge_catches_wrong_student_and_non_measurable():
    v = judge_goal("Alex Chen will get better at reading over time.", expected_student=STUDENT)
    assert not v.ok
    assert any("student" in r for r in v.reasons)
    assert any("measurable" in r for r in v.reasons)


def test_audit_log_is_append_only_per_run():
    store = LocalStore()
    supervisor = Supervisor(store)
    supervisor.supervise(
        task_id="t1", student=STUDENT, prompt=PROMPT,
        primary=make_worker("document_drafter", "loop", student=STUDENT),
        fallback=make_worker("backup_drafter", "none", student=STUDENT),
    )
    audit_rows = store.list("audit")
    # Every audit row carries a run_id and a monotonic seq (never rewritten).
    assert audit_rows
    seqs = [r["seq"] for r in audit_rows]
    assert seqs == sorted(seqs)
