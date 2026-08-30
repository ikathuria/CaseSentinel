"""Firestore-backed Store for the deployed build (mandated Google Cloud infra).

Behind the same ``Store`` interface as LocalStore, so nothing else changes. Used
when ``STORE_BACKEND=firestore``. The Firestore client is imported lazily so the
local/offline build needs no GCP dependency.
"""

from __future__ import annotations

from typing import Any

from .base import Store


class FirestoreStore(Store):
    def __init__(self, project_id: str | None = None, prefix: str = "casesentinel"):
        # Lazy import so the offline build never requires google-cloud-firestore.
        from google.cloud import firestore  # type: ignore

        self._firestore = firestore
        self._db = firestore.Client(project=project_id) if project_id else firestore.Client()
        self._prefix = prefix

    def _col(self, collection: str):
        return self._db.collection(f"{self._prefix}_{collection}")

    def append(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        stored = dict(record)
        # Server timestamp gives a reliable ordering key for list().
        stored["_created"] = self._firestore.SERVER_TIMESTAMP
        _, ref = self._col(collection).add(stored)
        stored.pop("_created", None)
        stored.setdefault("id", ref.id)
        return stored

    def list(self, collection: str) -> list[dict[str, Any]]:
        docs = self._col(collection).order_by("_created").stream()
        out: list[dict[str, Any]] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data.pop("_created", None)
            out.append(data)
        return out
