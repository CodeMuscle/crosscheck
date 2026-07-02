from fastapi.testclient import TestClient
from crosscheck.api import app, set_contradiction_source


def test_contradictions_endpoint_returns_confirmed():
    # Inject a fake graph + stub judge so no LLM/network is used.
    fake_nodes = [
        ("n1", {"name": "FooDB", "source": "srcA", "timestamp": "2021"}),
        ("n2", {"name": "50k"}),
        ("n3", {"name": "FooDB", "source": "srcD", "timestamp": "2024"}),
        ("n4", {"name": "10k"}),
    ]
    fake_edges = [("n1", "n2", "throughput_is", {}), ("n3", "n4", "throughput_is", {})]
    set_contradiction_source(
        graph=lambda: (fake_nodes, fake_edges),
        judge=lambda pair: (True, "conflict"),
    )
    client = TestClient(app)
    resp = client.get("/contradictions")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["entity"] == "FooDB"
