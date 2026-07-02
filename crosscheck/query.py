"""Query wrapper over cognee.search with citations. cognee imported lazily."""
import asyncio

from crosscheck.config import DATASET


def ask(question):
    import cognee
    from cognee import SearchType

    result = asyncio.get_event_loop().run_until_complete(
        cognee.search(
            question,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[DATASET],
            include_references=True,
        )
    )
    return {"answer": result, "references": getattr(result, "references", None)}
