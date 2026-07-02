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
