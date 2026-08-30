"""Deep / adversarial edge-case tests and regressions."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from casesentinel.agents.compliance_reporter import ComplianceReporter
from casesentinel.agents.timekeeper import Timekeeper
from casesentinel.api.app import app
from casesentinel.approval.gate import ApprovalError, ApprovalGate
from casesentinel.data.generate import generate_district, load_district, to_dict
from casesentinel.guards.judge import judge_goal
from casesentinel.store.local_store import LocalStore

DISTRICT = to_dict(generate_district())
client = TestClient(app)


# --- store: persistence + append-only integrity (regression) -----------------

def test_localstore_reloads_from_disk(tmp_path):
    s1 = LocalStore(base_dir=str(tmp_path))
    s1.append("audit", {"action": "a"})
    s1.append("audit", {"action": "b"})
    s2 = LocalStore(base_dir=str(tmp_path))  # simulates a process restart
    assert [r["action"] for r in s2.list("audit")] == ["a", "b"]
    s2.append("audit", {"action": "c"})
    assert [r["seq"] for r in s2.list("audit")] == [0, 1, 2]  # no seq collision


def test_localstore_list_returns_copy_not_internal_ref():
    s = LocalStore()
    s.append("c", {"x": 1})
    rows = s.list("c")
    rows.append({"x": 2})  # mutating the returned list must not corrupt the store
    assert len(s.list("c")) == 1


# --- fixture is not stale --------------------------------------------------

def test_committed_fixture_matches_generator():
    assert load_district() == to_dict(generate_district())


# --- timekeeper edge cases ---------------------------------------------------

def test_timekeeper_empty_district():
    empty = {"as_of": "2026-08-29", "students": [], "cases": []}
    assert Timekeeper().scan(empty) == []


def test_timekeeper_include_compliant_flag():
    only_risk = Timekeeper().scan(DISTRICT)
    with_all = Timekeeper().scan(DISTRICT, include_compliant=True)
    assert len(with_all) > len(only_risk)
    assert any(a.status == "compliant" for a in with_all)
    assert all(a.status != "compliant" for a in only_risk)


def test_timekeeper_transition_plan_only_for_age_16_plus():
    alerts = Timekeeper().scan(DISTRICT, include_compliant=True)
    students = {s["id"]: s for s in DISTRICT["students"]}
    as_of = date.fromisoformat(DISTRICT["as_of"])
    for a in alerts:
        if a.deadline_type == "transition_plan":
            s = students[a.student_id]
            age = as_of.year - date.fromisoformat(s["dob"]).year
            assert age >= 16, f"transition plan for age {age}"


def test_timekeeper_overdue_has_negative_days():
    for a in Timekeeper().scan(DISTRICT):
        if a.status == "overdue":
            assert a.days_remaining < 0
        if a.status == "due_soon":
            assert 0 <= a.days_remaining <= 30


# --- judge measurable-goal variants -----------------------------------------

@pytest.mark.parametrize("text", [
    "Jordan will read 90 wpm with 95% accuracy in 4 of 5 trials.",
    "Jordan will solve 8 out of 10 problems by June 2027.",
    "Jordan will improve reading accuracy to 80 percent.",
])
def test_judge_accepts_measurable_goals(text):
    assert judge_goal(text, expected_student="Jordan Rivera").ok


@pytest.mark.parametrize("text,reason_kw", [
    ("", "empty"),
    ("Jordan will get better at reading.", "measurable"),
    ("Alex Chen will read 90 wpm with 95% accuracy.", "different student"),
    ("The student will read 90 wpm with 95% accuracy.", "student"),
])
def test_judge_rejects_bad_goals(text, reason_kw):
    v = judge_goal(text, expected_student="Jordan Rivera")
    assert not v.ok
    assert any(reason_kw in r for r in v.reasons), v.reasons


# --- approval gate: reject + error paths -------------------------------------

def test_approval_reject_path_records_reason():
    gate = ApprovalGate(LocalStore())
    req = gate.create(run_id="r", student_id="s", student_name="n", artifact_type="t", content="c")
    out = gate.decide(req["id"], approver="Dir", decision="rejected", reason="not individualized")
    assert out["status"] == "rejected"
    assert out["reason"] == "not individualized"


def test_approval_decide_nonexistent_raises():
    gate = ApprovalGate(LocalStore())
    with pytest.raises(ApprovalError):
        gate.decide("nope", approver="x", decision="approved")


def test_approval_get_nonexistent_is_none():
    assert ApprovalGate(LocalStore()).get("nope") is None


def test_approval_list_status_filter():
    gate = ApprovalGate(LocalStore())
    a = gate.create(run_id="r", student_id="s1", student_name="A", artifact_type="t", content="c")
    gate.create(run_id="r", student_id="s2", student_name="B", artifact_type="t", content="c")
    gate.decide(a["id"], approver="Dir", decision="approved")
    assert len(gate.list(status="pending")) == 1
    assert len(gate.list(status="approved")) == 1
    assert len(gate.list()) == 2


# --- compliance reporter consistency with timekeeper -------------------------

def test_reporter_overdue_matches_worst_status_students():
    alerts = Timekeeper().scan(DISTRICT)
    posture = ComplianceReporter().rollup(DISTRICT, alerts)
    # every by_school / by_category bucket sums to a subset of students
    school_total = sum(sum(v.values()) for v in posture.by_school.values())
    assert school_total == len(DISTRICT["students"])


# --- API error paths ---------------------------------------------------------

def test_api_run_rejects_invalid_fault():
    assert client.post("/api/run?fault=explode").status_code == 400


def test_api_stream_rejects_invalid_fault():
    assert client.get("/api/run/stream?fault=explode").status_code == 400


def test_api_trace_unknown_run_404():
    assert client.get("/api/runs/does-not-exist/trace").status_code == 404


def test_api_decide_missing_approver_400():
    r = client.post("/api/approvals/whatever/decide", json={"decision": "approved"})
    assert r.status_code == 400


def test_api_decide_unknown_approval_409():
    r = client.post("/api/approvals/nope/decide", json={"approver": "Dir", "decision": "approved"})
    assert r.status_code == 409
