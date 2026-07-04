"""Gap finder: rank under-connected graph nodes, generate grounded next questions.

A "gap" is a node the graph knows about but has barely connected to anything
else — the copilot proposes what to research next to fill it in. Questions are
grounded in each node's actual neighbours so a weak local model stays on topic
instead of inventing unrelated subjects.
"""

# Cap neighbours fed into a prompt: enough to anchor the topic, not so many the
# prompt balloons or a hub's context drowns the node itself.
_MAX_CONTEXT = 8


def _degree_and_neighbors(nodes, edges):
    """Return (degree, neighbor_names, names) keyed by node id, in one edge pass."""
    names = {node_id: props.get("name", node_id) for node_id, props in nodes}
    degree = {node_id: 0 for node_id, _ in nodes}
    neighbors = {node_id: [] for node_id, _ in nodes}
    for src, tgt, _rel, _props in edges:
        if src in degree:
            degree[src] += 1
            if tgt in names:
                neighbors[src].append(names[tgt])
        if tgt in degree:
            degree[tgt] += 1
            if src in names:
                neighbors[tgt].append(names[src])
    return degree, neighbors, names


def _thin_ids(degree, top_n):
    """Node ids ordered by ascending degree; ties keep input order (stable sort)."""
    return sorted(degree, key=lambda nid: degree[nid])[:top_n]


def rank_thin_nodes(nodes, edges, top_n=5):
    """Names of the least-connected nodes, most-thin first."""
    degree, _neighbors, names = _degree_and_neighbors(nodes, edges)
    return [names[nid] for nid in _thin_ids(degree, top_n)]


def default_llm_ask(name, context):
    """Ask the LLM for ONE research question about `name`, grounded in `context`.

    `context` is the list of neighbour names; passing it (rather than the bare
    name) is what keeps a small local model from drifting to unrelated topics.
    """
    import asyncio

    from cognee.infrastructure.llm.LLMGateway import LLMGateway

    related = ", ".join(context) if context else "nothing else yet"
    return asyncio.run(
        LLMGateway.acreate_structured_output(
            text_input=(
                f"Topic: '{name}'. In our knowledge base it is currently linked only to: "
                f"{related}. Write ONE concise research question that would deepen our "
                f"understanding of '{name}' specifically. The question must mention "
                f"'{name}' and must not introduce any unrelated subject."
            ),
            system_prompt=(
                "You propose a single focused research question, grounded strictly in "
                "the given topic and its related terms. Never introduce unrelated subjects."
            ),
            response_model=str,
        )
    )


def find_gaps(nodes, edges, ask=None, top_n=5):
    """One grounded research question per thin node.

    `ask(name, context)` is injectable for offline testing; `context` is the
    node's deduplicated neighbour names (capped at _MAX_CONTEXT).
    """
    ask = ask or default_llm_ask
    degree, neighbors, names = _degree_and_neighbors(nodes, edges)
    questions = []
    for nid in _thin_ids(degree, top_n):
        context = list(dict.fromkeys(neighbors[nid]))[:_MAX_CONTEXT]
        questions.append(ask(names[nid], context))
    return questions
