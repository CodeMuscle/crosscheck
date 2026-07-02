"""Thin FastAPI app wrapping the units; reuses cognee's graph visualization."""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from crosscheck.graph_access import triplets_from_graph
from crosscheck.contradictions import find_contradictions
from crosscheck.gaps import find_gaps
from crosscheck import ingest as ingest_mod
from crosscheck.query import ask as ask_query
from crosscheck.preset.benchmarks import PRESET

app = FastAPI(title="Crosscheck")
_STATIC = Path(__file__).parent / "static"

# Injectable sources (overridden in tests); default to the live graph + LLM judge.
_graph_fn = ingest_mod.current_graph
_judge_fn = None  # None -> find_contradictions uses default_llm_judge


def set_contradiction_source(graph=None, judge="__keep__"):
    global _graph_fn, _judge_fn
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
    nodes, edges = _graph_fn()
    tri = triplets_from_graph(nodes, edges)
    return [asdict(c) for c in find_contradictions(tri, judge=_judge_fn)]


@app.get("/gaps")
def gaps_route():
    nodes, edges = _graph_fn()
    return {"questions": find_gaps(nodes, edges)}
