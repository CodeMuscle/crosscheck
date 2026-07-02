"""Query wrapper over cognee.search with citations. cognee imported lazily."""
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
