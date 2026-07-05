"""Argus web app (port 8020, or mounted at /argus). Cached preset leakage +
live audit of pasted docs + CSV export + a tabbed static panel.

The preset findings are computed ONCE with Crosscheck's real judge and cached, so
the demo never recomputes on camera. `POST /audit` runs the same pipeline live on
documents you paste (heavier — real LLM extraction). Crosscheck (:8010) untouched.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from crosscheck.claims import extract_claims
from crosscheck.contradictions import default_llm_judge
from argus.audit import build_leakage
from argus.preset import PRESET_CLAIMS
from argus.report import findings_to_csv

app = FastAPI(title="Argus")
_STATIC = Path(__file__).parent / "static"
_cache = None


class AuditRequest(BaseModel):
    sources: list[dict]  # [{id, timestamp, text}, ...]


def _preset_result():
    global _cache
    if _cache is None:
        _cache = build_leakage(PRESET_CLAIMS, judge=default_llm_judge)
    return _cache


@app.get("/leakage")
def leakage():
    """Cached leakage for the built-in demo pack."""
    return _preset_result()


@app.post("/audit")
def audit(req: AuditRequest):
    """Run the leakage pipeline live on pasted documents (real LLM extraction)."""
    claims = extract_claims(req.sources)
    return build_leakage(claims, judge=default_llm_judge)


@app.get("/export.csv")
def export_csv():
    """Download the demo-pack findings as a CSV for a finance team."""
    csv_text = findings_to_csv(_preset_result())
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=argus-leakage.csv"},
    )


@app.get("/")
def index():
    return FileResponse(_STATIC / "index.html")
