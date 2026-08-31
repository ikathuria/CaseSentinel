"""Evidence Ingestor — normalizes messy source docs into structured evidence.

Generative in production (Gemini flash-lite reads progress notes, therapy memos,
and behavior logs and returns a clean clinical summary). Offline it degrades to a
deterministic normalization so the pipeline stays runnable with no API key.
"""

from __future__ import annotations

import re

from google.adk.agents import LlmAgent

from ..models.factory import MODEL_LITE, has_gemini_key
from .base import Evidence
from .runtime import run_text

# Light shorthand expansion for the offline normalizer.
_SHORTHAND = {
    r"\babt\b": "about",
    r"\bw/\b": "with",
    r"\bre:\b": "regarding",
    r"\bfyi\b": "note",
    r"\b2x30\b": "twice weekly for 30 minutes",
    r"\bconvo\b": "conversation",
    r"\bwk\b": "week",
}


def _clean(text: str) -> str:
    out = text
    for pat, repl in _SHORTHAND.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\?{2,}", "", out)  # drop "???" noise
    out = re.sub(r"\s+", " ", out).strip()
    return out


class EvidenceIngestor:
    name = "evidence_ingestor"

    async def run(self, student: dict, docs: list[dict]) -> Evidence:
        student_name = f"{student['first_name']} {student['last_name']}"
        doc_ids = [d["id"] for d in docs]

        if not docs:
            return Evidence(student["id"], student_name, "No source documents on file.", [])

        if has_gemini_key():
            summary = await self._summarize_with_gemini(student_name, docs)
        else:
            summary = self._summarize_deterministic(student_name, docs)

        return Evidence(student["id"], student_name, summary, doc_ids)

    async def _summarize_with_gemini(self, student_name: str, docs: list[dict]) -> str:
        joined = "\n".join(f"[{d['type']} {d['date']}] {d['text']}" for d in docs)
        agent = LlmAgent(
            name=self.name,
            model=MODEL_LITE,
            instruction=(
                "You normalize messy special-education source documents into a concise, "
                "factual clinical summary (3-4 sentences). Expand shorthand, keep every "
                "measurable datum (e.g. words-per-minute, accuracy %), and never invent facts."
            ),
        )
        try:
            text = await run_text(agent, f"Summarize the evidence for {student_name}:\n{joined}")
        except Exception:
            # Gemini unavailable (rate limit, quota, outage) — degrade gracefully to
            # the deterministic normalizer instead of failing the whole pipeline.
            return self._summarize_deterministic(student_name, docs)
        return text.strip() or self._summarize_deterministic(student_name, docs)

    def _summarize_deterministic(self, student_name: str, docs: list[dict]) -> str:
        lines = [f"{d['type'].replace('_', ' ')}: {_clean(d['text'])}" for d in docs]
        return f"Evidence for {student_name} normalized from {len(docs)} source document(s). " + " | ".join(lines)
