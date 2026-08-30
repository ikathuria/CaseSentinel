"""FastAPI app — the surface the dashboard talks to.

Endpoints:
  GET  /health
  GET  /api/district                       synthetic district (schools, cases, docs)
  POST /api/run?fault=none|loop|hallucination|tool_error
                                           run the multi-agent pipeline once
  GET  /api/approvals?status=pending       list approval requests
  POST /api/approvals/{id}/decide          approve/reject a draft (named human)
  GET  /api/audit?run_id=...               audit entries (optionally one run)
  GET  /api/incidents                      logged failure incidents
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..approval.gate import ApprovalError
from ..data.generate import load_district
from ..orchestrator import CaseSentinelOrchestrator
from ..store.local_store import LocalStore

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

app = FastAPI(title="CaseSentinel API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# File-backed store so audit/approvals persist across requests during a demo.
_DATA_DIR = os.environ.get("CASESENTINEL_DATA_DIR", str(Path(__file__).resolve().parents[3] / ".data"))
store = LocalStore(base_dir=_DATA_DIR)
orchestrator = CaseSentinelOrchestrator(store)
gate = orchestrator.gate

_VALID_FAULTS = {"none", "loop", "hallucination", "tool_error", "transient_tool_error"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "casesentinel"}


@app.get("/api/district")
def district() -> dict:
    return load_district()


@app.post("/api/run")
async def run(fault: str = Query("none")) -> dict:
    if fault not in _VALID_FAULTS:
        raise HTTPException(400, f"invalid fault {fault!r}; expected one of {sorted(_VALID_FAULTS)}")
    result = await orchestrator.run_pipeline_async(load_district(), inject_fault=fault)  # type: ignore[arg-type]
    return result.to_dict()


@app.get("/api/approvals")
def approvals(status: str | None = Query(None)) -> list[dict]:
    return gate.list(status=status)


@app.post("/api/approvals/{approval_id}/decide")
def decide(approval_id: str, body: dict = Body(...)) -> dict:
    decision = body.get("decision")
    approver = body.get("approver")
    if not approver:
        raise HTTPException(400, "approver is required")
    try:
        return gate.decide(
            approval_id, approver=approver, decision=decision, reason=body.get("reason")
        )
    except ApprovalError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/audit")
def audit(run_id: str | None = Query(None)) -> list[dict]:
    rows = store.list("audit")
    if run_id:
        rows = [r for r in rows if r.get("run_id") == run_id]
    return rows


@app.get("/api/incidents")
def incidents() -> list[dict]:
    return store.list("incidents")


@app.get("/api/runs/{run_id}/trace")
def run_trace(run_id: str) -> dict:
    """The full audit trail + incidents for one pipeline run (the due-process record)."""
    audit = [r for r in store.list("audit") if r.get("run_id") == run_id]
    inc = [r for r in store.list("incidents") if r.get("run_id") == run_id]
    if not audit:
        raise HTTPException(404, f"no such run: {run_id}")
    return {"run_id": run_id, "audit_trail": audit, "incidents": inc}
