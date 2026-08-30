"""M3 gate: generalized guards + retry/reroute/escalate recovery policy."""

from __future__ import annotations

import asyncio

import pytest

from casesentinel.guards.callbacks import goal_judge, nonempty_judge
from casesentinel.guards.failure_injection import make_worker
from casesentinel.guards.loop_guard import run_guarded
from casesentinel.guards.supervisor import Supervisor
from casesentinel.store.local_store import LocalStore

STUDENT = "Jordan Rivera"
PROMPT = f"Draft one measurable annual reading goal for {STUDENT}."


def _supervise(primary_fault, fallback_fault="none"):
    supervisor = Supervisor(LocalStore())
    return supervisor.supervise(
        task_id="t",
        student=STUDENT,
        prompt=PROMPT,
        primary=make_worker("document_drafter", primary_fault, student=STUDENT),
        fallback=make_worker("backup_drafter", fallback_fault, student=STUDENT),
    )


# --- generalized guard is agent-agnostic ------------------------------------

def test_loop_guard_detects_each_execution_fault():
    loop = run_guarded_sync(make_worker("w", "loop", student=STUDENT))
    assert loop.fault == "loop"
    crash = run_guarded_sync(make_worker("w", "tool_error", student=STUDENT))
    assert crash.fault == "tool_error"
    ok = run_guarded_sync(make_worker("w", "none", student=STUDENT))
    assert ok.fault is None and ok.output


def run_guarded_sync(agent):
    return asyncio.run(run_guarded(agent, PROMPT, max_iterations=5))


def test_judges():
    ok, _ = goal_judge(STUDENT)("Jordan will read 90 wpm with 95% accuracy by June.")
    assert ok
    bad, reason = goal_judge(STUDENT)("Alex Chen will improve.")
    assert not bad and reason
    assert nonempty_judge("x")[0] is True
    assert nonempty_judge("  ")[0] is False


# --- recovery policy ---------------------------------------------------------

def test_transient_fault_recovered_by_retry_no_fallback():
    result = _supervise("transient_tool_error")
    assert result.status == "resolved"
    assert result.action_taken == "retried_recovered"
    assert result.served_by == "document_drafter"  # primary recovered on retry
    assert len(result.incidents) == 1
    assert result.incidents[0]["fault_type"] == "tool_error"
    actions = [e["action"] for e in result.audit_trail]
    assert "retry" in actions and "reroute" not in actions


@pytest.mark.parametrize("fault", ["loop", "hallucination"])
def test_systematic_fault_reroutes_without_retry(fault):
    result = _supervise(fault)
    assert result.status == "resolved"
    assert result.action_taken == "reroute_to_fallback"
    assert result.served_by == "backup_drafter"
    actions = [e["action"] for e in result.audit_trail]
    assert "reroute" in actions and "retry" not in actions


def test_tool_error_retries_then_reroutes():
    # CrashingWorker fails on retry too -> falls through to the fallback.
    result = _supervise("tool_error")
    assert result.status == "resolved"
    assert result.action_taken == "reroute_to_fallback"
    assert result.served_by == "backup_drafter"
    actions = [e["action"] for e in result.audit_trail]
    assert "retry" in actions and "reroute" in actions


def test_escalates_to_human_when_fallback_also_fails():
    result = _supervise("hallucination", fallback_fault="loop")
    assert result.status == "needs_human"
    assert result.action_taken == "escalate_to_human"
    assert result.output is None
    actions = [e["action"] for e in result.audit_trail]
    assert "escalate_to_human" in actions
    assert any(i["action_taken"] == "escalate_to_human" for i in result.incidents)
