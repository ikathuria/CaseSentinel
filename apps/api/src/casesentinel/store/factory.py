"""Store factory — picks the backend from STORE_BACKEND (local | firestore)."""

from __future__ import annotations

import os
from pathlib import Path

from .base import Store
from .local_store import LocalStore


def get_store() -> Store:
    backend = os.environ.get("STORE_BACKEND", "local").lower()
    if backend == "firestore":
        from .firestore_store import FirestoreStore

        return FirestoreStore(project_id=os.environ.get("FIRESTORE_PROJECT_ID") or None)
    data_dir = os.environ.get(
        "CASESENTINEL_DATA_DIR", str(Path(__file__).resolve().parents[4] / ".data")
    )
    return LocalStore(base_dir=data_dir)
