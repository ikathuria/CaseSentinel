"""Live Gemini smoke test — only runs when an API key is configured."""

from __future__ import annotations

import pytest

from casesentinel.models.factory import has_gemini_key
from casesentinel.spike.smoke_gemini import _run_sync


@pytest.mark.skipif(not has_gemini_key(), reason="no GOOGLE_API_KEY / GEMINI_API_KEY set")
def test_live_gemini_returns_text():
    text = _run_sync()
    assert text and text.strip()
