from argus.audit import build_leakage
from argus.preset import PRESET_CLAIMS, EXPECTED_TOTAL

# Offline stub judge: every structural candidate is a real conflict.
STUB_JUDGE = lambda pair: (True, "values differ")


def test_build_leakage_totals_and_ranks():
    result = build_leakage(PRESET_CLAIMS, judge=STUB_JUDGE)
    assert result["total_at_risk"] == EXPECTED_TOTAL
    amounts = [f["amount"] for f in result["findings"]]
    assert amounts == [2400.0, 2000.0, 900.0]  # descending
    assert result["findings"][0]["category"] == "Discount not applied"
    assert "entity" in result["findings"][0] and "note" in result["findings"][0]
