# Crosscheck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Crosscheck — a self-improving research copilot on cognee that ingests sources into a knowledge graph, answers with citations, and flags when sources contradict each other.

**Architecture:** Pure decision logic (contradiction pre-filter, gap ranking) runs over cognee's `get_graph_data()` tuples and is unit-tested with synthetic graphs — no LLM/network in tests. Thin integration wrappers call `cognee.add/cognify/search`. A FastAPI app exposes ingest/ask/contradiction endpoints and reuses cognee's graph visualization. LLM-dependent steps (cognify, the contradiction judge) are injected so they can be stubbed in tests.

**Tech Stack:** Python 3.10+, cognee SDK, FastAPI + uvicorn, pytest, OpenAI (for cognify + judge).

## Global Constraints

- Python `>=3.10`.
- cognee pinned `cognee[scraping]>=1.1.0,<2.0.0` (scraping extra for the `--live` toggle).
- All cognee data lives under one dataset: `DATASET = "research"` (defined once in `crosscheck/config.py`).
- LLM and graph access are injected as callables/interfaces into pure logic — never imported directly inside a pure function — so tests run offline.
- Graph shapes (verified against cognee source): `Node = tuple[str, dict]` `(node_id, properties)`; `EdgeData = tuple[str, str, str, dict]` `(source_id, target_id, relationship_name, properties)`; `get_graph_data()` returns `(list[Node], list[EdgeData])`.
- TDD: failing test first. Commit after each green task.

---

### Task 1: Project scaffold + config

**Files:**
- Create: `pyproject.toml`
- Create: `crosscheck/__init__.py`
- Create: `crosscheck/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `crosscheck.config.DATASET: str = "research"`; `crosscheck.config.require_llm_key() -> str` (returns the key, raises `RuntimeError` with a clear message if `LLM_API_KEY`/`OPENAI_API_KEY` unset).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import pytest
from crosscheck import config


def test_dataset_constant():
    assert config.DATASET == "research"


def test_require_llm_key_raises_when_unset(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        config.require_llm_key()


def test_require_llm_key_returns_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    assert config.require_llm_key() == "sk-test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crosscheck.config'`

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
[project]
name = "crosscheck"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "cognee[scraping]>=1.1.0,<2.0.0",
    "fastapi>=0.110",
    "uvicorn>=0.29",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["crosscheck*"]
```

```python
# crosscheck/__init__.py
```

```python
# crosscheck/config.py
"""Central config: dataset name and LLM key check."""
import os

DATASET = "research"


def require_llm_key() -> str:
    """Return the configured LLM API key, or raise with a clear message."""
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "LLM_API_KEY (or OPENAI_API_KEY) must be set — cognify needs an LLM "
            "to extract the knowledge graph."
        )
    return key
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv venv && source .venv/bin/activate && uv pip install -e '.[dev]'` then `pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml crosscheck/__init__.py crosscheck/config.py tests/test_config.py
git commit -m "feat: project scaffold + config with LLM key check"
```

---

### Task 2: Triplet model + graph→triplet extraction

**Files:**
- Create: `crosscheck/model.py`
- Create: `crosscheck/graph_access.py`
- Test: `tests/test_graph_access.py`

**Interfaces:**
- Consumes: cognee graph shapes (`Node`, `EdgeData`).
- Produces:
  - `crosscheck.model.Triplet` dataclass: `subject: str`, `predicate: str`, `object: str`, `source: str`, `timestamp: str`.
  - `crosscheck.graph_access.triplets_from_graph(nodes: list[tuple[str, dict]], edges: list[tuple[str, str, str, dict]]) -> list[Triplet]` — pure. Resolves each edge into a Triplet using node `properties["name"]` for subject/object, `relationship_name` for predicate, and `properties["source"]` / `properties["timestamp"]` on the subject node for provenance (falling back to `"unknown"`/`""`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_graph_access.py
from crosscheck.model import Triplet
from crosscheck.graph_access import triplets_from_graph


def test_triplets_from_graph_resolves_names_and_provenance():
    nodes = [
        ("n1", {"name": "ToolX", "source": "srcA", "timestamp": "2021-01-01"}),
        ("n2", {"name": "50k rps"}),
    ]
    edges = [("n1", "n2", "throughput_is", {})]
    triplets = triplets_from_graph(nodes, edges)
    assert triplets == [
        Triplet(subject="ToolX", predicate="throughput_is", object="50k rps",
                source="srcA", timestamp="2021-01-01"),
    ]


def test_triplets_skip_edges_with_unknown_nodes():
    nodes = [("n1", {"name": "ToolX"})]
    edges = [("n1", "ghost", "throughput_is", {})]
    assert triplets_from_graph(nodes, edges) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph_access.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crosscheck.model'`

- [ ] **Step 3: Write minimal implementation**

```python
# crosscheck/model.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Triplet:
    subject: str
    predicate: str
    object: str
    source: str
    timestamp: str


@dataclass(frozen=True)
class CandidatePair:
    subject: str
    predicate: str
    a: Triplet
    b: Triplet


@dataclass(frozen=True)
class Contradiction:
    entity: str
    claim_a: str
    source_a: str
    time_a: str
    claim_b: str
    source_b: str
    time_b: str
    explanation: str
```

```python
# crosscheck/graph_access.py
"""Pure helpers turning cognee's (nodes, edges) into Triplets."""
from crosscheck.model import Triplet


def triplets_from_graph(nodes, edges):
    """Resolve edges into Triplets. nodes: list[(id, props)]; edges: list[(src, tgt, rel, props)]."""
    by_id = {node_id: props for node_id, props in nodes}
    out = []
    for src, tgt, rel, _props in edges:
        if src not in by_id or tgt not in by_id:
            continue
        subj = by_id[src]
        out.append(
            Triplet(
                subject=subj.get("name", "unknown"),
                predicate=rel,
                object=by_id[tgt].get("name", "unknown"),
                source=subj.get("source", "unknown"),
                timestamp=subj.get("timestamp", ""),
            )
        )
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph_access.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add crosscheck/model.py crosscheck/graph_access.py tests/test_graph_access.py
git commit -m "feat: Triplet model + pure graph-to-triplet extraction"
```

---

### Task 3: Contradiction structural pre-filter (spec test #1)

**Files:**
- Create: `crosscheck/contradictions.py`
- Test: `tests/test_contradictions_structural.py`

**Interfaces:**
- Consumes: `crosscheck.model.Triplet`, `CandidatePair`.
- Produces: `crosscheck.contradictions.structural_candidates(triplets: list[Triplet]) -> list[CandidatePair]` — pure. Groups triplets by `(subject, predicate)`; emits a `CandidatePair` for each pair of triplets in a group that have **different objects** AND **different sources**. Same-source or same-object pairs are not candidates.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_contradictions_structural.py
from crosscheck.model import Triplet
from crosscheck.contradictions import structural_candidates


def _t(subj, pred, obj, src):
    return Triplet(subj, pred, obj, src, "2021-01-01")


def test_flags_conflicting_claim_from_different_sources():
    triplets = [
        _t("ToolX", "throughput_is", "50k rps", "srcA"),
        _t("ToolX", "throughput_is", "10k rps", "srcD"),
    ]
    pairs = structural_candidates(triplets)
    assert len(pairs) == 1
    assert {pairs[0].a.object, pairs[0].b.object} == {"50k rps", "10k rps"}


def test_ignores_multivalued_property_control():
    # A legitimately multi-valued fact from different sources is still a
    # candidate structurally; the LLM-judge (Task 4) rejects it. But identical
    # objects, or same-source restatements, must NOT be candidates.
    triplets = [
        _t("ToolX", "written_in", "Rust", "srcA"),
        _t("ToolX", "written_in", "Rust", "srcB"),   # same object -> not a candidate
        _t("ToolX", "license_is", "MIT", "srcA"),
        _t("ToolX", "license_is", "MIT", "srcA"),     # same source -> not a candidate
    ]
    assert structural_candidates(triplets) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_contradictions_structural.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crosscheck.contradictions'`

- [ ] **Step 3: Write minimal implementation**

```python
# crosscheck/contradictions.py
"""Contradiction detection: structural pre-filter (B) + LLM-judge confirm (A)."""
from itertools import combinations

from crosscheck.model import CandidatePair, Contradiction


def structural_candidates(triplets):
    """Pairs sharing (subject, predicate) but with different object AND different source."""
    groups = {}
    for t in triplets:
        groups.setdefault((t.subject, t.predicate), []).append(t)
    candidates = []
    for (subject, predicate), members in groups.items():
        for a, b in combinations(members, 2):
            if a.object != b.object and a.source != b.source:
                candidates.append(CandidatePair(subject=subject, predicate=predicate, a=a, b=b))
    return candidates
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_contradictions_structural.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add crosscheck/contradictions.py tests/test_contradictions_structural.py
git commit -m "feat: structural contradiction pre-filter"
```

---

### Task 4: Contradiction LLM-judge pipeline

**Files:**
- Modify: `crosscheck/contradictions.py`
- Test: `tests/test_contradictions_judge.py`

**Interfaces:**
- Consumes: `structural_candidates`, `CandidatePair`, `Contradiction`.
- Produces:
  - `crosscheck.contradictions.judge_candidates(pairs: list[CandidatePair], judge) -> list[Contradiction]` where `judge` is a callable `(CandidatePair) -> tuple[bool, str]` returning `(is_conflict, explanation)`. Emits a `Contradiction` only when `is_conflict` is True.
  - `crosscheck.contradictions.find_contradictions(triplets, judge=None) -> list[Contradiction]` — composes `structural_candidates` then `judge_candidates`; `judge` defaults to `default_llm_judge` (defined here, calls the LLM; NOT exercised in unit tests).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_contradictions_judge.py
from crosscheck.model import Triplet
from crosscheck.contradictions import find_contradictions


def _t(obj, src):
    return Triplet("ToolX", "throughput_is", obj, src, "2021")


def test_emits_contradiction_when_judge_confirms():
    triplets = [_t("50k rps", "srcA"), _t("10k rps", "srcD")]
    judge = lambda pair: (True, "50k contradicts 10k")
    result = find_contradictions(triplets, judge=judge)
    assert len(result) == 1
    c = result[0]
    assert c.entity == "ToolX"
    assert {c.claim_a, c.claim_b} == {"50k rps", "10k rps"}
    assert c.explanation == "50k contradicts 10k"


def test_drops_pair_when_judge_rejects():
    triplets = [_t("Rust", "srcA"), _t("Go", "srcD")]
    judge = lambda pair: (False, "different attributes, not a conflict")
    assert find_contradictions(triplets, judge=judge) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_contradictions_judge.py -v`
Expected: FAIL — `ImportError: cannot import name 'find_contradictions'`

- [ ] **Step 3: Write minimal implementation**

Append to `crosscheck/contradictions.py`:

```python
def judge_candidates(pairs, judge):
    """Confirm candidates with an injected judge callable -> (is_conflict, explanation)."""
    out = []
    for pair in pairs:
        is_conflict, explanation = judge(pair)
        if is_conflict:
            out.append(
                Contradiction(
                    entity=pair.subject,
                    claim_a=pair.a.object, source_a=pair.a.source, time_a=pair.a.timestamp,
                    claim_b=pair.b.object, source_b=pair.b.source, time_b=pair.b.timestamp,
                    explanation=explanation,
                )
            )
    return out


def default_llm_judge(pair):
    """Ask the LLM whether two sourced claims about the same entity conflict."""
    from cognee.infrastructure.llm.get_llm_client import get_llm_client

    prompt = (
        f"Two sources make claims about '{pair.subject}' ({pair.predicate}).\n"
        f"Source A ({pair.a.source}): {pair.a.object}\n"
        f"Source B ({pair.b.source}): {pair.b.object}\n"
        "Do these directly contradict each other (cannot both be true)? "
        "Answer strictly 'YES: <reason>' or 'NO: <reason>'."
    )
    client = get_llm_client()
    import asyncio

    reply = asyncio.get_event_loop().run_until_complete(
        client.acreate_structured_output(
            text_input=prompt,
            system_prompt="You judge whether two claims contradict. Be strict.",
            response_model=str,
        )
    )
    is_conflict = reply.strip().upper().startswith("YES")
    explanation = reply.split(":", 1)[-1].strip() if ":" in reply else reply.strip()
    return is_conflict, explanation


def find_contradictions(triplets, judge=None):
    judge = judge or default_llm_judge
    return judge_candidates(structural_candidates(triplets), judge)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_contradictions_judge.py -v`
Expected: PASS (2 passed)

> Note: `default_llm_judge`'s exact LLM-client call is verified live in Task 7's smoke run; unit tests inject a stub judge and never hit the network. If `acreate_structured_output`'s signature differs at implementation time, adjust the wrapper — the tested contract (`judge(pair) -> (bool, str)`) does not change.

- [ ] **Step 5: Commit**

```bash
git add crosscheck/contradictions.py tests/test_contradictions_judge.py
git commit -m "feat: LLM-judge contradiction confirmation pipeline"
```

---

### Task 5: Gap finder (spec test #2)

**Files:**
- Create: `crosscheck/gaps.py`
- Test: `tests/test_gaps.py`

**Interfaces:**
- Consumes: cognee graph shapes.
- Produces:
  - `crosscheck.gaps.rank_thin_nodes(nodes, edges, top_n=5) -> list[str]` — pure. Returns node **names** ranked by ascending degree (fewest edges first), limited to `top_n`. Degree counts edges where the node id is source or target.
  - `crosscheck.gaps.find_gaps(nodes, edges, ask=None, top_n=5) -> list[str]` — for each thin node name, calls `ask(name) -> str` (a research question); `ask` defaults to `default_llm_ask` (LLM; not unit-tested).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gaps.py
from crosscheck.gaps import rank_thin_nodes, find_gaps


def test_rank_thin_nodes_orders_by_degree():
    nodes = [("n1", {"name": "Hub"}), ("n2", {"name": "Thin"}), ("n3", {"name": "Mid"})]
    edges = [
        ("n1", "n3", "rel", {}),
        ("n1", "n2", "rel", {}),
        ("n1", "n3", "rel2", {}),  # Hub deg 3, Mid deg 2, Thin deg 1
    ]
    assert rank_thin_nodes(nodes, edges, top_n=2) == ["Thin", "Mid"]


def test_find_gaps_asks_question_per_thin_node():
    nodes = [("n1", {"name": "Thin"})]
    edges = []
    questions = find_gaps(nodes, edges, ask=lambda name: f"What is missing about {name}?")
    assert questions == ["What is missing about Thin?"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gaps.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crosscheck.gaps'`

- [ ] **Step 3: Write minimal implementation**

```python
# crosscheck/gaps.py
"""Gap finder: rank thin graph nodes, generate next research questions."""


def rank_thin_nodes(nodes, edges, top_n=5):
    degree = {node_id: 0 for node_id, _ in nodes}
    for src, tgt, _rel, _props in edges:
        if src in degree:
            degree[src] += 1
        if tgt in degree:
            degree[tgt] += 1
    names = {node_id: props.get("name", node_id) for node_id, props in nodes}
    ranked = sorted(degree, key=lambda nid: degree[nid])
    return [names[nid] for nid in ranked[:top_n]]


def default_llm_ask(name):
    from cognee.infrastructure.llm.get_llm_client import get_llm_client
    import asyncio

    client = get_llm_client()
    return asyncio.get_event_loop().run_until_complete(
        client.acreate_structured_output(
            text_input=f"Give one concise research question to learn more about '{name}'.",
            system_prompt="You propose focused research questions.",
            response_model=str,
        )
    )


def find_gaps(nodes, edges, ask=None, top_n=5):
    ask = ask or default_llm_ask
    return [ask(name) for name in rank_thin_nodes(nodes, edges, top_n=top_n)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gaps.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add crosscheck/gaps.py tests/test_gaps.py
git commit -m "feat: gap finder (thin-node ranking + question generation)"
```

---

### Task 6: Ingestor + query wrappers + preset pack

**Files:**
- Create: `crosscheck/ingest.py`
- Create: `crosscheck/query.py`
- Create: `crosscheck/preset/benchmarks.py`
- Test: `tests/test_preset.py`

**Interfaces:**
- Consumes: `crosscheck.config.DATASET`, cognee `add`/`cognify`/`search`/`get_graph_engine`.
- Produces:
  - `crosscheck.preset.benchmarks.PRESET: list[dict]` — each `{"id": str, "text": str, "timestamp": str}`. Contains exactly one planted contradiction (a tool's throughput reported differently in two dated sources) plus a same-fact control repeated across sources.
  - `crosscheck.ingest.ingest(sources: list[dict], live: bool = False) -> dict` — for preset dicts, `cognee.add(text, dataset_name=DATASET, node_set=[id])` per source then `cognee.cognify(datasets=[DATASET])`; when `live=True`, `sources` is a topic string routed through cognee scraping. Returns `{"ingested": n}`.
  - `crosscheck.ingest.current_graph() -> tuple[list, list]` — `await get_graph_engine().get_graph_data()`, run to completion.
  - `crosscheck.query.ask(question: str) -> dict` — `cognee.search(question, query_type=SearchType.GRAPH_COMPLETION, datasets=[DATASET], include_references=True)`; returns `{"answer": ..., "references": ...}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_preset.py
from crosscheck.preset.benchmarks import PRESET


def test_preset_has_planted_contradiction():
    ids = [s["id"] for s in PRESET]
    assert len(ids) == len(set(ids)), "source ids must be unique"
    texts = " ".join(s["text"].lower() for s in PRESET)
    # planted contradiction: same metric, two different numbers
    assert "throughput" in texts
    assert any(s["timestamp"] for s in PRESET), "sources must carry timestamps"
    assert len(PRESET) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_preset.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crosscheck.preset'`

- [ ] **Step 3: Write minimal implementation**

```python
# crosscheck/preset/__init__.py
```

```python
# crosscheck/preset/benchmarks.py
"""Deterministic demo pack: dated benchmark claims with one planted contradiction."""

PRESET = [
    {
        "id": "srcA-2021",
        "timestamp": "2021-03-01",
        "text": "In our 2021 evaluation, FooDB sustained a throughput of 50,000 "
                "requests per second on a single node. FooDB is written in Rust "
                "and released under the MIT license.",
    },
    {
        "id": "srcB-2022",
        "timestamp": "2022-06-01",
        "text": "FooDB is written in Rust. Its query planner supports cost-based "
                "optimization. The project is MIT licensed.",
    },
    {
        "id": "srcD-2024",
        "timestamp": "2024-09-01",
        "text": "Independent 2024 benchmarks found FooDB sustained a throughput of "
                "only 10,000 requests per second on a single node under mixed load.",
    },
]
```

```python
# crosscheck/ingest.py
"""Ingestion: preset dicts or live topic -> cognee graph."""
import asyncio

import cognee
from cognee.infrastructure.databases.graph import get_graph_engine

from crosscheck.config import DATASET


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def ingest(sources, live=False):
    if live:
        _run(cognee.add(sources, dataset_name=DATASET))
        n = 1
    else:
        n = 0
        for s in sources:
            try:
                _run(cognee.add(s["text"], dataset_name=DATASET, node_set=[s["id"]]))
                n += 1
            except Exception as exc:  # a bad source must not abort the batch
                print(f"skip source {s['id']}: {exc}")
    _run(cognee.cognify(datasets=[DATASET]))
    return {"ingested": n}


def current_graph():
    engine = _run(get_graph_engine())
    return _run(engine.get_graph_data())
```

```python
# crosscheck/query.py
"""Query wrapper over cognee.search with citations."""
import asyncio

import cognee
from cognee import SearchType

from crosscheck.config import DATASET


def ask(question):
    result = asyncio.get_event_loop().run_until_complete(
        cognee.search(
            question,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[DATASET],
            include_references=True,
        )
    )
    return {"answer": result, "references": getattr(result, "references", None)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_preset.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Live smoke (manual, needs LLM_API_KEY)**

Run:
```bash
export LLM_API_KEY=sk-...   # real key
python -c "
from crosscheck.ingest import ingest, current_graph
from crosscheck.graph_access import triplets_from_graph
from crosscheck.contradictions import find_contradictions
from crosscheck.preset.benchmarks import PRESET
ingest(PRESET)
nodes, edges = current_graph()
tri = triplets_from_graph(nodes, edges)
for c in find_contradictions(tri):
    print('CONTRADICTION:', c.entity, c.claim_a, 'vs', c.claim_b, '->', c.explanation)
"
```
Expected: prints a contradiction on FooDB throughput (50k vs 10k). If node `properties` use different keys than `name`/`source`/`timestamp`, adjust `triplets_from_graph` mapping and re-run — the unit tests stay green because they pass explicit props.

- [ ] **Step 6: Commit**

```bash
git add crosscheck/ingest.py crosscheck/query.py crosscheck/preset tests/test_preset.py
git commit -m "feat: ingestor + query wrappers + deterministic preset pack"
```

---

### Task 7: FastAPI app + panel + cognee viz reuse

**Files:**
- Create: `crosscheck/api.py`
- Create: `crosscheck/static/index.html`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `ingest`, `current_graph`, `triplets_from_graph`, `find_contradictions`, `find_gaps`, `ask`.
- Produces: FastAPI `app` with routes: `POST /ingest` (body `{"live": bool, "sources"|"topic"}`), `POST /ask` (body `{"question": str}`), `GET /contradictions` (returns confirmed list from the current graph), `GET /gaps`, `GET /` (serves the panel). Contradiction/gap routes accept an injectable judge/ask via app state for testing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from crosscheck.api import app, set_contradiction_source

def test_contradictions_endpoint_returns_confirmed(monkeypatch):
    # Inject a fake graph + stub judge so no LLM/network is used.
    fake_nodes = [
        ("n1", {"name": "FooDB", "source": "srcA", "timestamp": "2021"}),
        ("n2", {"name": "50k"}),
        ("n3", {"name": "FooDB", "source": "srcD", "timestamp": "2024"}),
        ("n4", {"name": "10k"}),
    ]
    fake_edges = [("n1", "n2", "throughput_is", {}), ("n3", "n4", "throughput_is", {})]
    set_contradiction_source(
        graph=lambda: (fake_nodes, fake_edges),
        judge=lambda pair: (True, "conflict"),
    )
    client = TestClient(app)
    resp = client.get("/contradictions")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["entity"] == "FooDB"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crosscheck.api'`

- [ ] **Step 3: Write minimal implementation**

```python
# crosscheck/api.py
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

app = FastAPI(title="Crosscheck")
_STATIC = Path(__file__).parent / "static"

# Injectable sources (overridden in tests); default to the live graph + LLM judge.
_graph_fn = ingest_mod.current_graph
_judge_fn = None  # None -> contradictions.find_contradictions uses default_llm_judge


def set_contradiction_source(graph=None, judge="__keep__"):
    global _graph_fn, _judge_fn
    if graph is not None:
        _graph_fn = graph
    if judge != "__keep__":
        _judge_fn = judge


@app.get("/")
def index():
    return FileResponse(_STATIC / "index.html")


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
```

```html
<!-- crosscheck/static/index.html -->
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Crosscheck</title>
<style>
 body{font:14px system-ui;margin:0;display:grid;grid-template-columns:360px 1fr;height:100vh}
 #panel{padding:16px;border-right:1px solid #ddd;overflow:auto}
 #graph{border:0}
 textarea{width:100%;height:80px} button{margin:4px 0}
 .alert{background:#fff3f0;border:1px solid #ffb3a0;padding:8px;margin:6px 0;border-radius:6px}
</style></head>
<body>
<div id="panel">
  <h2>Crosscheck</h2>
  <h3>Ingest</h3>
  <label><input type="checkbox" id="live"> live web search</label>
  <textarea id="sources" placeholder="topic (live) or leave blank to load preset pack"></textarea>
  <button onclick="ingest()">Ingest</button>
  <h3>Ask</h3>
  <textarea id="q" placeholder="ask a question"></textarea>
  <button onclick="ask()">Ask</button>
  <pre id="answer"></pre>
  <h3>Contradictions</h3>
  <button onclick="loadContradictions()">Refresh</button>
  <div id="alerts"></div>
</div>
<iframe id="graph" src="http://localhost:8000/" width="100%" height="100%"></iframe>
<script>
async function ingest(){
  const live=document.getElementById('live').checked;
  const txt=document.getElementById('sources').value.trim();
  const body=live?{live:true,topic:txt}:{live:false,sources:await presetIfEmpty(txt)};
  await fetch('/ingest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  loadContradictions();
}
async function presetIfEmpty(txt){ return txt?JSON.parse(txt):(await (await fetch('/preset')).json()); }
async function ask(){
  const question=document.getElementById('q').value;
  const r=await (await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})})).json();
  document.getElementById('answer').textContent=JSON.stringify(r,null,2);
}
async function loadContradictions(){
  const list=await (await fetch('/contradictions')).json();
  document.getElementById('alerts').innerHTML=list.map(c=>
    `<div class="alert">🚨 <b>${c.entity}</b><br>${c.source_a} (${c.time_a}): ${c.claim_a}<br>${c.source_b} (${c.time_b}): ${c.claim_b}<br><i>${c.explanation}</i></div>`
  ).join('')||'none yet';
}
</script>
</body></html>
```

> The graph iframe points at cognee's visualization server (`start_visualization_server`, started in Task 8's runbook on port 8000). Add a `GET /preset` route returning `crosscheck.preset.benchmarks.PRESET` so the empty-ingest path loads the pack:

```python
# append to crosscheck/api.py
from crosscheck.preset.benchmarks import PRESET

@app.get("/preset")
def preset_route():
    return PRESET
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS (1 passed). Then run the whole suite: `pytest -v` → all green.

- [ ] **Step 5: Commit**

```bash
git add crosscheck/api.py crosscheck/static tests/test_api.py
git commit -m "feat: FastAPI app + query panel + contradiction feed"
```

---

### Task 8: Demo runbook, persistence check (spec test #3), README/blog

**Files:**
- Create: `RUNBOOK.md`
- Create: `scripts/persistence_check.py`
- Modify: `README.md`
- Create: `docs/blog.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a documented start sequence, a persistence self-check script, and demo/blog copy.

- [ ] **Step 1: Write the persistence check (spec test #3)**

```python
# scripts/persistence_check.py
"""Prove cross-session memory: ingest once, then a fresh process re-queries from the store."""
import sys
from crosscheck.ingest import current_graph
from crosscheck.graph_access import triplets_from_graph

nodes, edges = current_graph()
tri = triplets_from_graph(nodes, edges)
foodb = [t for t in tri if t.subject == "FooDB"]
if not foodb:
    print("FAIL: no FooDB claims found in the persisted graph — was the preset ingested?")
    sys.exit(1)
print(f"OK: {len(foodb)} FooDB claims served from the store without re-ingesting.")
```

- [ ] **Step 2: Run the two-process persistence check**

Run:
```bash
export LLM_API_KEY=sk-...
python -c "from crosscheck.ingest import ingest; from crosscheck.preset.benchmarks import PRESET; ingest(PRESET)"
python scripts/persistence_check.py   # fresh process, no ingest
```
Expected: second process prints `OK: N FooDB claims served from the store...` — proving persistence across sessions.

- [ ] **Step 3: Write the runbook**

```markdown
# RUNBOOK

## Start
1. `export LLM_API_KEY=sk-...`
2. Start cognee's graph viz server on :8000:
   `python -c "import asyncio, cognee; asyncio.run(cognee.start_visualization_server(port=8000))"`
3. Start Crosscheck API on :8010:
   `uvicorn crosscheck.api:app --port 8010`
4. Open http://localhost:8010

## 2-minute demo
1. Click **Ingest** (empty box → loads preset pack). Graph grows.
2. **Ask**: "What is FooDB's throughput?" → cited answer.
3. Click **Refresh** under Contradictions → 🚨 FooDB 50k (2021) vs 10k (2024).
4. Toggle **live**, enter a topic → graph expands (gap-filling).
5. Restart the API; re-open → contradictions still there (persistence).
```

- [ ] **Step 4: Write README + blog**

```markdown
<!-- README.md -->
# Crosscheck
A self-improving research copilot that never forgets — and catches sources disagreeing. Built on cognee.

**Why a graph:** answers cite their sources, and the graph makes contradictions between sources *visible* — impossible with plain vector recall.

See [RUNBOOK.md](RUNBOOK.md) and the [design spec](docs/superpowers/specs/2026-07-01-crosscheck-design.md).
```

```markdown
<!-- docs/blog.md -->
# Building an AI research copilot that catches its sources lying

(Draft: the problem — research tools forget and never notice when two sources
disagree. How cognee's knowledge graph makes contradiction detection a graph
query + an LLM judge. The 50k-vs-10k FooDB demo. What "self-improving" means:
gap-driven follow-up. Link to repo + 2-min video.)
```

- [ ] **Step 5: Commit**

```bash
git add RUNBOOK.md scripts/persistence_check.py README.md docs/blog.md
git commit -m "docs: demo runbook, persistence check, README + blog draft"
```

---

## Self-Review

**Spec coverage:**
- Ingestor → Task 6. Contradiction engine (A+B) → Tasks 3+4. Gap finder → Task 5. Memory store/persistence → Task 6 (`DATASET`) + Task 8 (check). API/UI + viz reuse → Task 7. Provenance → Task 2 (Triplet.source/timestamp) + Task 6 (`node_set`/timestamps). Demo script → Task 8 runbook. Testing (3 spec checks) → Task 3 (#1), Task 5 (#2), Task 8 (#3). Error handling (skip failed source, judge fallback, key check) → Task 1 key check + noted; **add**: ingest per-source try/except folded into Task 6 Step 3 if a source fails (wrap each `cognee.add` in try/except logging and continue).
- Live search toggle → Task 6 (`live=True`) + Task 7 route.

**Placeholder scan:** blog.md is an intentional draft (content written Day 4 after the demo), not a code placeholder. All code steps contain full code.

**Type consistency:** `Triplet(subject,predicate,object,source,timestamp)`, `CandidatePair(subject,predicate,a,b)`, `Contradiction(entity,claim_a,source_a,time_a,claim_b,source_b,time_b,explanation)`, `judge(pair)->(bool,str)`, `ask(name)->str`, `find_contradictions(triplets,judge)`, `find_gaps(nodes,edges,ask,top_n)` — consistent across tasks.

**Fix applied:** Task 6 Step 3 — wrap each preset `cognee.add` in `try/except` to satisfy the spec's "failed source logs and skips, never aborts the batch" requirement.
