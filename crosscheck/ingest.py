"""Ingestion: preset dicts or live topic -> cognee graph.

cognee is imported lazily inside functions so importing this module (and the
FastAPI app that depends on it) does not require the full cognee stack — the
pure logic and API routing stay testable offline.
"""
import asyncio

from crosscheck.config import DATASET


def _defang_summarization():
    """Neutralize cognee's LLM chunk-summarization so weak local models can't
    abort cognify.

    cognee's `summarize_text` task demands schema-valid JSON (SummarizedContent
    with a required `description`) that small local models (llama3.1:8b) won't
    reliably emit — it nests `summary` and drops `description`, which raises even
    through BAML and kills the whole pipeline before the graph is built.

    Crosscheck reads the knowledge GRAPH (entities/relations/source/timestamp),
    never the chunk summaries, so we swap the whole summarize step for naive
    truncation. We patch the name `extract_graph_and_summarize` actually calls
    (it does `from cognee.tasks.summarization import summarize_text`), so no LLM
    summary request is ever issued. Graph extraction is untouched, making ingest
    robust on ANY model/provider.

    ponytail: naive-truncation summaries. Restore the real LLM call only if a
    feature ever starts consuming TextSummary.text.
    """
    from uuid import uuid5
    import cognee.tasks.graph.extract_graph_and_summarize as eg
    from cognee.tasks.summarization.models import TextSummary
    from cognee.modules.data.processing.document_types import DltRowDocument

    async def _naive_summarize(data_chunks, summarization_model=None):
        if not isinstance(data_chunks, list) or not data_chunks:
            return data_chunks
        non_dlt = [
            c for c in data_chunks
            if not isinstance(getattr(c, "is_part_of", None), DltRowDocument)
        ]
        dlt = [c for c in data_chunks if c not in non_dlt]
        if not non_dlt:
            return data_chunks
        summaries = [
            TextSummary(
                id=uuid5(c.id, "TextSummary"),
                made_from=c,
                source_chunk_id=str(c.id),
                belongs_to_set=c.belongs_to_set,
                text=(c.text or "")[:300],
                importance_weight=c.importance_weight,
            )
            for c in non_dlt
        ]
        return summaries + dlt

    eg.summarize_text = _naive_summarize


async def _ingest_async(sources, live):
    import cognee

    _defang_summarization()

    if live:
        await cognee.add(sources, dataset_name=DATASET)
        n = 1
    else:
        n = 0
        for s in sources:
            try:
                await cognee.add(s["text"], dataset_name=DATASET, node_set=[s["id"]])
                n += 1
            except Exception as exc:  # a bad source must not abort the batch
                print(f"skip source {s['id']}: {exc}")
    await cognee.cognify(datasets=[DATASET])
    return {"ingested": n}


def ingest(sources, live=False):
    return asyncio.run(_ingest_async(sources, live))


async def _graph_async():
    from cognee.infrastructure.databases.graph import get_graph_engine

    engine = await get_graph_engine()
    return await engine.get_graph_data()


def current_graph():
    return asyncio.run(_graph_async())
