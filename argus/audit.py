"""Turn claims into ranked leakage findings with a total at risk.

Reuses Crosscheck's find_contradictions (structural pre-filter + judge) unchanged,
then attaches a dollar impact to each and ranks by money at risk.
"""
from dataclasses import asdict

from crosscheck.contradictions import find_contradictions
from argus.impact import dollar_impact


def build_leakage(claims, judge=None):
    """{total_at_risk, findings[]} — findings sorted by amount desc, None last."""
    findings = []
    for c in find_contradictions(claims, judge=judge):
        impact = dollar_impact(c)
        findings.append({**asdict(c), **impact})
    findings.sort(key=lambda f: (f["amount"] is not None, f["amount"] or 0), reverse=True)
    total = sum(f["amount"] for f in findings if f["amount"] is not None)
    return {"total_at_risk": total, "findings": findings}
