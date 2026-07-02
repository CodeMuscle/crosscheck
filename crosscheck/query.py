"""Query wrapper over cognee.search with citations. cognee imported lazily.

NOTE: on a small local model cognee's search-completion path fails under BAML
(`Unsupported type for BAML mapping: str | None`). This endpoint is reliable on a
hosted model (Profile B/C in .env.example). The contradiction feed does not
depend on it — see RUNBOOK.
"""
import asyncio

from crosscheck.config import DATASET


async def _ask_async(question):
    import cognee
    from cognee import SearchType

    return await cognee.search(
        question,
        query_type=SearchType.GRAPH_COMPLETION,
        datasets=[DATASET],
        include_references=True,
    )


def ask(question):
    result = asyncio.run(_ask_async(question))
    return {"answer": result, "references": getattr(result, "references", None)}
