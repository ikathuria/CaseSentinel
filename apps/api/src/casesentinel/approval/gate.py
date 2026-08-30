"""Human approval gate — a first-class object, not an afterthought.

Under IDEA the IEP team's signature makes a document legal; AI only accelerates
drafting. Every consequential draft becomes a ``pending`` ApprovalRequest that only
a named human can move to ``approved``/``rejected`` — and every transition is
written to the audit log. State is derived from append-only records (creation +
immutable decision events) so the store and audit trail stay tamper-evident.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..audit.log import AuditLog
from ..store.base import Store

REQUESTS = "approvals"
DECISIONS = "approval_decisions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalError(Exception):
    pass


class ApprovalGate:
    def __init__(self, store: Store):
        self._store = store

    def create(
        self,
        *,
        run_id: str,
        student_id: str,
        student_name: str,
        artifact_type: str,
        content: str,
        audit: AuditLog | None = None,
    ) -> dict[str, Any]:
        request = self._store.append(
            REQUESTS,
            {
                "id": uuid.uuid4().hex,
                "run_id": run_id,
                "student_id": student_id,
                "student_name": student_name,
                "artifact_type": artifact_type,
                "content": content,
                "created_ts": _now(),
            },
        )
        if audit:
            audit.record(
                "approval_requested",
                agent="approval_gate",
                detail={"approval_id": request["id"], "student": student_name,
                        "artifact_type": artifact_type},
            )
        return self.get(request["id"])

    def decide(
        self,
        approval_id: str,
        *,
        approver: str,
        decision: str,
        reason: str | None = None,
        audit: AuditLog | None = None,
    ) -> dict[str, Any]:
        if decision not in ("approved", "rejected"):
            raise ApprovalError(f"invalid decision: {decision!r}")
        current = self.get(approval_id)
        if current is None:
            raise ApprovalError(f"no such approval: {approval_id}")
        if current["status"] != "pending":
            raise ApprovalError(f"approval {approval_id} already {current['status']}")

        self._store.append(
            DECISIONS,
            {
                "approval_id": approval_id,
                "decision": decision,
                "approver": approver,
                "reason": reason,
                "decided_ts": _now(),
            },
        )
        run_id = current["run_id"]
        log = audit or AuditLog(self._store, run_id=run_id)
        log.record(
            "approval_decision",
            agent="approval_gate",
            detail={"approval_id": approval_id, "decision": decision,
                    "approver": approver, "reason": reason},
        )
        return self.get(approval_id)

    def get(self, approval_id: str) -> dict[str, Any] | None:
        base = next(
            (r for r in self._store.list(REQUESTS) if r["id"] == approval_id), None
        )
        if base is None:
            return None
        return self._fold(base)

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        rows = [self._fold(r) for r in self._store.list(REQUESTS)]
        if status:
            rows = [r for r in rows if r["status"] == status]
        return rows

    def _fold(self, base: dict[str, Any]) -> dict[str, Any]:
        """Reconstruct current state from creation + latest decision."""
        record = dict(base)
        record.setdefault("status", "pending")
        record.update({"status": "pending", "approver": None, "reason": None, "decided_ts": None})
        decisions = [d for d in self._store.list(DECISIONS) if d["approval_id"] == base["id"]]
        if decisions:
            last = decisions[-1]
            record.update(
                status=last["decision"],
                approver=last["approver"],
                reason=last["reason"],
                decided_ts=last["decided_ts"],
            )
        return record
