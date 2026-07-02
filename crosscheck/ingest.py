"""Ingestion: preset dicts or live topic -> cognee graph.

cognee is imported lazily inside functions so importing this module (and the
FastAPI app that depends on it) does not require the full cognee stack — the
pure logic and API routing stay testable offline.
"""
import asyncio

from crosscheck.config import DATASET


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def ingest(sources, live=False):
    import cognee

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
    from cognee.infrastructure.databases.graph import get_graph_engine

    engine = _run(get_graph_engine())
    return _run(engine.get_graph_data())
