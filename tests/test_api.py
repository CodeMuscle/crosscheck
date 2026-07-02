from fastapi.testclient import TestClient
from crosscheck.api import app, set_contradiction_source
from crosscheck.model import Triplet


def test_contradictions_endpoint_returns_confirmed():
    # Inject fake claims + stub judge so no LLM/network is used.
    fake_claims = [
        Triplet("foodb", "throughput", "50k", "srcA", "2021"),
        Triplet("foodb", "throughput", "10k", "srcD", "2024"),
    ]
    set_contradiction_source(
        claims=lambda: fake_claims,
        judge=lambda pair: (True, "conflict"),
    )
    client = TestClient(app)
    resp = client.get("/contradictions")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["entity"] == "foodb"
