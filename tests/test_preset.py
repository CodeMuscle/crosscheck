from crosscheck.preset.benchmarks import PRESET


def test_preset_has_planted_contradiction():
    ids = [s["id"] for s in PRESET]
    assert len(ids) == len(set(ids)), "source ids must be unique"
    texts = " ".join(s["text"].lower() for s in PRESET)
    assert "throughput" in texts
    assert any(s["timestamp"] for s in PRESET), "sources must carry timestamps"
    assert len(PRESET) >= 3
