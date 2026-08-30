"""Append-only audit log and incident recorder.

Every consequential action and every detected agent failure is written here. This
is the due-process paper trail — the reason CaseSentinel exists (see PROJECT.md).
Records are never mutated after being written.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from ..store.base import Store

AUDIT = "audit"
INCIDENTS = "incidents"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditLog:
    """Scoped to a single supervised run (``run_id``).

    An optional ``on_event`` callback fires for every audit entry as it is written
    — used by the SSE endpoint to stream the live trace to the dashboard.
    """

    def __init__(
        self,
        store: Store,
        run_id: str | None = None,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ):
        self._store = store
        self.run_id = run_id or uuid.uuid4().hex
        self._on_event = on_event

    def record(
        self,
        action: str,
        *,
        agent: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append one audit entry (e.g. delegate, kill, reroute, approve)."""
        entry = self._store.append(
            AUDIT,
            {
                "run_id": self.run_id,
                "ts": _now(),
                "action": action,
                "agent": agent,
                "detail": detail or {},
            },
        )
        if self._on_event:
            self._on_event(entry)
        return entry

    def record_incident(
        self,
        *,
        agent: str,
        fault_type: str,
        detection: str,
        action_taken: str,
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a structured failure incident and mirror it into the audit log."""
        incident = self._store.append(
            INCIDENTS,
            {
                "id": uuid.uuid4().hex,
                "run_id": self.run_id,
                "ts": _now(),
                "agent": agent,
                "fault_type": fault_type,
                "detection": detection,
                "action_taken": action_taken,
                "detail": detail or {},
            },
        )
        self.record(
            "incident",
            agent=agent,
            detail={
                "fault_type": fault_type,
                "detection": detection,
                "action_taken": action_taken,
                "incident_id": incident["id"],
            },
        )
        return incident

    def entries(self) -> list[dict[str, Any]]:
        return [e for e in self._store.list(AUDIT) if e.get("run_id") == self.run_id]

    def incidents(self) -> list[dict[str, Any]]:
        return [i for i in self._store.list(INCIDENTS) if i.get("run_id") == self.run_id]
