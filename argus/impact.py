"""Deterministic dollar impact for a numeric contradiction. No LLM.

A leakage finding is a contradiction whose two claims are dollar amounts; the
money at risk is their difference. The category is inferred from keywords in the
entity so the panel can badge it. Non-money contradictions return amount=None
(shown as "needs review", never as a dollar figure).
"""
import re

_MONEY = re.compile(r"-?\$\s*([\d,]+(?:\.\d+)?)")


def _parse_money(s):
    """First dollar amount (a $-prefixed number) as a float, or None if there is none.

    Requires the '$' so non-money digits like "Net-30" are not misread as money.
    """
    if s is None:
        return None
    m = _MONEY.search(str(s))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _category(entity):
    e = (entity or "").lower()
    if "credit" in e or "discount" in e:
        return "Discount not applied"
    if "tax" in e:
        return "Tax overbill"
    if "line total" in e or "po" in e or "price" in e:
        return "Price mismatch"
    return "Amount mismatch"


def dollar_impact(contradiction):
    """{amount, category, note} for a contradiction; amount=None if not monetary."""
    a = _parse_money(contradiction.claim_a)
    b = _parse_money(contradiction.claim_b)
    if a is None or b is None:
        return {"amount": None, "category": "Needs review",
                "note": "Non-numeric conflict — review manually."}
    amount = abs(a - b)
    if a >= b:
        hi_src, hi_val, lo_src, lo_val = contradiction.source_a, a, contradiction.source_b, b
    else:
        hi_src, hi_val, lo_src, lo_val = contradiction.source_b, b, contradiction.source_a, a
    note = f"{hi_src} (${hi_val:,.0f}) exceeds {lo_src} (${lo_val:,.0f}) by ${amount:,.0f}."
    return {"amount": amount, "category": _category(contradiction.entity), "note": note}
