"""FastAPI app — the surface the dashboard talks to.

M1 ships a health check and a read-only district endpoint so the web shell can
prove connectivity. Agent runs, the approval gate, the live trace stream (SSE),
and failure injection are added in later milestones.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..data.generate import load_district

app = FastAPI(title="CaseSentinel API", version="0.1.0")

# The dashboard runs on the Vite dev server in development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "casesentinel"}


@app.get("/api/district")
def district() -> dict:
    """The synthetic district (schools, caseloads, cases, messy docs)."""
    return load_district()
