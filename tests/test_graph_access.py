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
