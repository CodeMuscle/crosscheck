from crosscheck.model import Triplet
from crosscheck.contradictions import find_contradictions


def _t(obj, src):
    return Triplet("ToolX", "throughput_is", obj, src, "2021")


def test_emits_contradiction_when_judge_confirms():
    triplets = [_t("50k rps", "srcA"), _t("10k rps", "srcD")]
    judge = lambda pair: (True, "50k contradicts 10k")
    result = find_contradictions(triplets, judge=judge)
    assert len(result) == 1
    c = result[0]
    assert c.entity == "ToolX"
    assert {c.claim_a, c.claim_b} == {"50k rps", "10k rps"}
    assert c.explanation == "50k contradicts 10k"


def test_drops_pair_when_judge_rejects():
    triplets = [_t("Rust", "srcA"), _t("Go", "srcD")]
    judge = lambda pair: (False, "different attributes, not a conflict")
    assert find_contradictions(triplets, judge=judge) == []
