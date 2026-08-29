"""Storage abstraction.

The whole system reads/writes through this interface so the audit log, approval
gate, and case state can live in a local JSON file for tests/offline demos and in
Firestore for the deployed build — without any caller change (PLAN.md decision).
"""

from __future__ import annotations

import abc
from typing import Any


class Store(abc.ABC):
    """Append-oriented document store keyed by collection name."""

    @abc.abstractmethod
    def append(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        """Append a record to a collection and return it (with any added id)."""

    @abc.abstractmethod
    def list(self, collection: str) -> list[dict[str, Any]]:
        """Return all records in a collection, in insertion order."""
