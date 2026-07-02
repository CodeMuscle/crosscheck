from crosscheck.model import Triplet
from crosscheck.contradictions import structural_candidates


def _t(subj, pred, obj, src):
    return Triplet(subj, pred, obj, src, "2021-01-01")


def test_flags_conflicting_claim_from_different_sources():
    triplets = [
        _t("ToolX", "throughput_is", "50k rps", "srcA"),
        _t("ToolX", "throughput_is", "10k rps", "srcD"),
    ]
    pairs = structural_candidates(triplets)
    assert len(pairs) == 1
    assert {pairs[0].a.object, pairs[0].b.object} == {"50k rps", "10k rps"}


def test_ignores_multivalued_property_control():
    triplets = [
        _t("ToolX", "written_in", "Rust", "srcA"),
        _t("ToolX", "written_in", "Rust", "srcB"),   # same object -> not a candidate
        _t("ToolX", "license_is", "MIT", "srcA"),
        _t("ToolX", "license_is", "MIT", "srcA"),     # same source -> not a candidate
    ]
    assert structural_candidates(triplets) == []
