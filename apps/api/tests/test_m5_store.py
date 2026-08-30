"""M5: store factory selects the backend; firestore adapter imports lazily."""

from __future__ import annotations

import importlib

from casesentinel.store.base import Store
from casesentinel.store.factory import get_store
from casesentinel.store.local_store import LocalStore


def test_factory_defaults_to_local(monkeypatch):
    monkeypatch.delenv("STORE_BACKEND", raising=False)
    store = get_store()
    assert isinstance(store, LocalStore)
    assert isinstance(store, Store)


def test_firestore_adapter_imports_without_gcp():
    # Module must import even without google-cloud-firestore installed
    # (the client import is lazy, inside __init__).
    mod = importlib.import_module("casesentinel.store.firestore_store")
    assert hasattr(mod, "FirestoreStore")
