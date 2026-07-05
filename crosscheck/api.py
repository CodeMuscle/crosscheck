"""Thin FastAPI app wrapping the units; reuses cognee's graph visualization."""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from crosscheck.contradictions import find_contradictions
from crosscheck.claims import extract_claims
from crosscheck.gaps import find_gaps
from crosscheck import ingest as ingest_mod
from crosscheck.query import ask as ask_query
from crosscheck.preset.benchmarks import PRESET

app = FastAPI(title="Crosscheck")
_STATIC = Path(__file__).parent / "static"

# Contradictions read faithful claims extracted from source text (the cognee KG
# drops numeric values, so it can't feed the engine). Claims are LLM-derived and
# static for the preset, so cache them — refreshes stay instant.
_claims_cache = None


def _default_claims():
    global _claims_cache
    if _claims_cache is None:
        _claims_cache = extract_claims(PRESET)
    return _claims_cache


# Injectable sources (overridden in tests); default to preset claims + LLM judge.
_graph_fn = ingest_mod.current_graph
_claims_fn = _default_claims
_judge_fn = None  # None -> find_contradictions uses default_llm_judge


def set_contradiction_source(claims=None, graph=None, judge="__keep__"):
    global _claims_fn, _graph_fn, _judge_fn
    if claims is not None:
        _claims_fn = claims
    if graph is not None:
        _graph_fn = graph
    if judge != "__keep__":
        _judge_fn = judge


@app.get("/")
def index():
    return FileResponse(_STATIC / "index.html")


@app.get("/preset")
def preset_route():
    return PRESET


@app.post("/ingest")
def ingest_route(body: dict):
    if body.get("live"):
        return ingest_mod.ingest(body["topic"], live=True)
    return ingest_mod.ingest(body["sources"], live=False)


@app.post("/ask")
def ask_route(body: dict):
    return ask_query(body["question"])


@app.get("/contradictions")
def contradictions_route():
    return [asdict(c) for c in find_contradictions(_claims_fn(), judge=_judge_fn)]


@app.get("/gaps")
def gaps_route():
    nodes, edges = _graph_fn()
    return {"questions": find_gaps(nodes, edges)}


# Two fixes patched into cognee's generated viz HTML (kept here, not forked into
# cognee): (1) the Node Type legend sits at bottom:20px z-90, the same row as the
# bottom-center selector at z-100, so they overlap — lift the legend above it;
# (2) dark-mode edges draw at alpha 0.15 on a near-black canvas → nearly invisible,
# so bump the edge alphas. Each replace is a no-op if the source string moves.
_GRAPH_PATCHES = [
    # (1) overlap: raise legend clear of the bottom-center controls + above them
    ("#legend{\n  position:fixed;bottom:20px;left:20px;z-index:90;",
     "#legend{\n  position:fixed;bottom:76px;left:20px;z-index:101;"),
    # (2) dark-mode edge visibility: the node-connecting edges draw at 0.08 alpha
    # on a near-black canvas → invisible. Bump the idle alpha and the dark
    # line width. (Hover/search dimming keeps its own 0.02 branch, untouched.)
    ("var nAlpha=hoveredNode?0.02:hasSearch?0.02:0.08;",
     "var nAlpha=hoveredNode?0.02:hasSearch?0.02:0.26;"),
    ("ctx.lineWidth=(_light ? 0.8 : 0.5)/scale;",
     "ctx.lineWidth=(_light ? 0.8 : 1)/scale;"),
]


@app.get("/graph")
async def graph_route():
    """Serve cognee's self-contained graph visualization (kept current on each load)."""
    import cognee

    html = await cognee.visualize_graph()
    for old, new in _GRAPH_PATCHES:
        html = html.replace(old, new)
    return HTMLResponse(html)
