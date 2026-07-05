from argus.audit import build_leakage
from argus.report import findings_to_csv

STUB_JUDGE = lambda pair: (True, "values differ")


def test_csv_has_header_rows_and_total():
    result = build_leakage(
        [], judge=STUB_JUDGE
    )
    # empty result still produces a valid header + total line
    csv_text = findings_to_csv(result)
    lines = [l for l in csv_text.splitlines() if l.strip()]
    assert lines[0].startswith("Issue,Item,At risk")
    assert lines[-1].startswith("TOTAL AT RISK (USD)")


def test_csv_row_per_finding():
    from argus.preset import PRESET_CLAIMS
    result = build_leakage(PRESET_CLAIMS, judge=STUB_JUDGE)
    csv_text = findings_to_csv(result)
    assert "Discount not applied" in csv_text
    assert "2400" in csv_text
    assert "5300" in csv_text
    # header + 3 findings + blank + total
    non_empty = [l for l in csv_text.splitlines() if l.strip()]
    assert len(non_empty) == 1 + 3 + 1
