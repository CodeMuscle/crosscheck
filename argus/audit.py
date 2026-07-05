"""Turn claims into ranked leakage findings with a total at risk.

Reuses Crosscheck's structural pre-filter + judge unchanged, attaches a dollar
impact to each confirmed contradiction, and ranks by money at risk. Also reports
the pipeline stage counts so the UI can show how the output was produced.
"""
from dataclasses import asdict

from crosscheck.contradictions import find_contradictions, structural_candidates
from argus.impact import dollar_impact


def build_leakage(claims, judge=None):
    """{total_at_risk, findings[], stages{}} — findings sorted by amount desc, None last.

    stages: {claims, candidates, confirmed} — how many claims went in, how many
    same-fact pairs the structural pre-filter flagged, how many the judge confirmed.
    """
    candidates = structural_candidates(claims)
    findings = []
    for c in find_contradictions(claims, judge=judge):
        impact = dollar_impact(c)
        findings.append({**asdict(c), **impact})
    findings.sort(key=lambda f: (f["amount"] is not None, f["amount"] or 0), reverse=True)
    total = sum(f["amount"] for f in findings if f["amount"] is not None)
    stages = {"claims": len(claims), "candidates": len(candidates), "confirmed": len(findings)}
    return {"total_at_risk": total, "findings": findings, "stages": stages}
