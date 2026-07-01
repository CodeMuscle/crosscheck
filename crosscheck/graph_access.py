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
