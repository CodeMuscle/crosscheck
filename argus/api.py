"""Argus web app (port 8020). Serves cached leakage findings + a static panel.

Findings are computed ONCE from the deterministic PRESET_CLAIMS using Crosscheck's
real LLM judge (only ~3 tiny judge calls), then cached — the demo never recomputes
on camera. Separate app; the Crosscheck server on :8010 is untouched.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from crosscheck.contradictions import default_llm_judge
from argus.audit import build_leakage
from argus.preset import PRESET_CLAIMS

app = FastAPI(title="Argus")
_STATIC = Path(__file__).parent / "static"
_cache = None


@app.get("/leakage")
def leakage():
    global _cache
    if _cache is None:
        _cache = build_leakage(PRESET_CLAIMS, judge=default_llm_judge)
    return _cache


@app.get("/")
def index():
    return FileResponse(_STATIC / "index.html")
