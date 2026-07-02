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
    import asyncio

    from cognee.infrastructure.llm.LLMGateway import LLMGateway

    return asyncio.run(
        LLMGateway.acreate_structured_output(
            text_input=f"Give one concise research question to learn more about '{name}'.",
            system_prompt="You propose focused research questions.",
            response_model=str,
        )
    )


def find_gaps(nodes, edges, ask=None, top_n=5):
    ask = ask or default_llm_ask
    return [ask(name) for name in rank_thin_nodes(nodes, edges, top_n=top_n)]
