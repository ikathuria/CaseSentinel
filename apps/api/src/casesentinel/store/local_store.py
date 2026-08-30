"""Local, append-only Store backed by JSONL files (one per collection).

Default backend for tests and the offline demo. Records are never mutated in
place — the audit log's integrity depends on append-only writes.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .base import Store


class LocalStore(Store):
    def __init__(self, base_dir: str | Path | None = None):
        # In-memory only when base_dir is None (fast, isolated tests).
        self._base_dir = Path(base_dir) if base_dir is not None else None
        self._mem: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.Lock()
        if self._base_dir is not None:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    def _load(self) -> None:
        """Load existing JSONL files so state survives a process restart."""
        assert self._base_dir is not None
        for path in sorted(self._base_dir.glob("*.jsonl")):
            collection = path.stem
            rows: list[dict[str, Any]] = []
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
            self._mem[collection] = rows

    def _path(self, collection: str) -> Path:
        assert self._base_dir is not None
        return self._base_dir / f"{collection}.jsonl"

    def append(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = self._mem.setdefault(collection, [])
            stored = dict(record)
            stored.setdefault("seq", len(rows))
            rows.append(stored)
            if self._base_dir is not None:
                with self._path(collection).open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(stored, ensure_ascii=False) + "\n")
            return stored

    def list(self, collection: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._mem.get(collection, []))
