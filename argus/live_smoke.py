"""End-to-end: preset claims -> real judge -> ranked leakage + total. Prints result."""
from crosscheck.contradictions import default_llm_judge
from argus.audit import build_leakage
from argus.preset import PRESET_CLAIMS

if __name__ == "__main__":
    result = build_leakage(PRESET_CLAIMS, judge=default_llm_judge)
    print(f"TOTAL AT RISK: ${result['total_at_risk']:,.0f}")
    for f in result["findings"]:
        amt = f"${f['amount']:,.0f}" if f["amount"] is not None else "review"
        print(f"  [{f['category']}] {amt} — {f['entity']}")
        print(f"     {f['source_a']} {f['claim_a']}  vs  {f['source_b']} {f['claim_b']}")
