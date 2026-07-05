"""Export leakage findings as a CSV an AP/finance team can act on."""
import csv
import io

_COLUMNS = [
    ("category", "Issue"),
    ("entity", "Item"),
    ("amount", "At risk (USD)"),
    ("source_a", "Source A"),
    ("time_a", "Date A"),
    ("claim_a", "Value A"),
    ("source_b", "Source B"),
    ("time_b", "Date B"),
    ("claim_b", "Value B"),
    ("note", "Detail"),
]


def findings_to_csv(result):
    """A leakage result dict -> CSV text (header row + one row per finding + total)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([label for _key, label in _COLUMNS])
    for f in result["findings"]:
        writer.writerow([f.get(key, "") for key, _label in _COLUMNS])
    writer.writerow([])
    writer.writerow(["TOTAL AT RISK (USD)", "", result.get("total_at_risk", 0)])
    return buf.getvalue()
