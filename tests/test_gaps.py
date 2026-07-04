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
    questions = find_gaps(nodes, edges, ask=lambda name, context: f"What is missing about {name}?")
    assert questions == ["What is missing about Thin?"]


def test_find_gaps_grounds_question_in_neighbours():
    """The thin node's neighbour names are passed as context (keeps a weak model on topic)."""
    nodes = [("n1", {"name": "FooDB"}), ("n2", {"name": "Rust"}), ("n3", {"name": "MIT"})]
    edges = [("n1", "n2", "written_in", {}), ("n1", "n3", "licensed_under", {})]
    seen = {}

    def ask(name, context):
        seen[name] = context
        return name

    # FooDB has degree 2; Rust and MIT each degree 1 (thinnest) -> asked first.
    find_gaps(nodes, edges, ask=ask, top_n=2)
    assert seen == {"Rust": ["FooDB"], "MIT": ["FooDB"]}


def test_find_gaps_dedupes_and_caps_context():
    """Repeated neighbours collapse; context never exceeds the cap."""
    from crosscheck.gaps import _MAX_CONTEXT

    nodes = [("hub", {"name": "Hub"})] + [(f"n{i}", {"name": f"N{i}"}) for i in range(_MAX_CONTEXT + 3)]
    # Every Ni links to Hub twice -> Hub's context would be duplicated and oversized.
    edges = [(f"n{i}", "hub", "rel", {}) for i in range(_MAX_CONTEXT + 3)] * 2
    seen = {}
    find_gaps(nodes, edges, ask=lambda name, context: seen.setdefault(name, context), top_n=99)
    assert len(seen["Hub"]) <= _MAX_CONTEXT
    assert len(seen["Hub"]) == len(set(seen["Hub"]))  # no duplicates
