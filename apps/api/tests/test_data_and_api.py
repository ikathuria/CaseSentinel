"""M1 gate: synthetic data has seeded violations; the API serves it."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from casesentinel.api.app import app
from casesentinel.data.generate import AS_OF, generate_district, load_district, to_dict

client = TestClient(app)


def test_district_has_seeded_violations():
    d = to_dict(generate_district())
    overdue = [c for c in d["cases"] if c["seeded_status"] == "overdue"]
    due_soon = [c for c in d["cases"] if c["seeded_status"] == "due_soon"]
    assert len(overdue) >= 1
    assert len(due_soon) >= 1


def test_overdue_dates_are_actually_past_as_of():
    d = to_dict(generate_district())
    by_id = {c["student_id"]: c for c in d["cases"]}
    overdue = [c for c in by_id.values() if c["seeded_status"] == "overdue"]
    for c in overdue:
        assert date.fromisoformat(c["annual_review_due"]) < AS_OF


def test_generation_is_deterministic():
    assert to_dict(generate_district()) == to_dict(generate_district())


def test_messy_documents_exist_for_ingestor():
    d = to_dict(generate_district())
    assert len(d["documents"]) >= 3
    assert all(doc["text"].strip() for doc in d["documents"])


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_district_endpoint_serves_students():
    r = client.get("/api/district")
    assert r.status_code == 200
    body = r.json()
    assert len(body["students"]) == len(load_district()["students"]) >= 1
