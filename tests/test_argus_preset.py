from crosscheck.contradictions import structural_candidates
from argus.preset import PRESET_CLAIMS, EXPECTED_TOTAL


def test_preset_yields_three_cross_source_candidates():
    cands = structural_candidates(PRESET_CLAIMS)
    assert len(cands) == 3
    # every candidate pairs two different sources
    assert all(c.a.source != c.b.source for c in cands)


def test_expected_total_is_sum_of_three_cases():
    assert EXPECTED_TOTAL == 5300.0
