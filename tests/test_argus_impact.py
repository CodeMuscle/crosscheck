from crosscheck.model import Contradiction
from argus.impact import dollar_impact, _parse_money


def _c(entity, a, sa, b, sb):
    return Contradiction(entity, a, sa, "t", b, sb, "t", "differ")


def test_parse_money():
    assert _parse_money("$2,400") == 2400.0
    assert _parse_money("$0") == 0.0
    assert _parse_money("Net-30 terms") is None


def test_discount_case():
    r = dollar_impact(_c("acme early-pay credit", "$2,400", "Contract", "$0", "Invoice"))
    assert r["amount"] == 2400.0
    assert r["category"] == "Discount not applied"


def test_price_case():
    r = dollar_impact(_c("po-3391 widget line total", "$10,000", "PO-3391", "$12,000", "Invoice"))
    assert r["amount"] == 2000.0
    assert r["category"] == "Price mismatch"


def test_tax_case():
    r = dollar_impact(_c("acme order tax", "$1,000", "Contract", "$1,900", "Invoice"))
    assert r["amount"] == 900.0
    assert r["category"] == "Tax overbill"


def test_non_money_is_none():
    r = dollar_impact(_c("payment terms", "Net-30", "Contract", "Net-60", "Invoice"))
    assert r["amount"] is None
    assert r["category"] == "Needs review"
