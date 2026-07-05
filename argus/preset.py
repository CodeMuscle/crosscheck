"""Argus demo pack: 3 planted spend-leakage cases as cross-source claims.

Each case is two claims that share (subject, predicate) but come from different
documents with different dollar values, so Crosscheck's structural pre-filter
groups them and the judge confirms a contradiction. Values are dollar-denominated
so the impact is a clean subtraction. DOCS carries the same facts as prose for
the graph/story; the served demo path uses PRESET_CLAIMS for determinism.
"""
from crosscheck.model import Triplet

# Case A: negotiated early-pay credit never applied. $2,400.
# Case B: invoice line total exceeds the PO. $2,000.
# Case C: tax charged above the contracted amount. $900.
PRESET_CLAIMS = [
    Triplet("acme early-pay credit", "amount due", "$2,400", "Contract ACME-2023", "2023-01-15"),
    Triplet("acme early-pay credit", "amount due", "$0", "Invoice INV-8842", "2024-06-03"),
    Triplet("po-3391 widget line total", "amount", "$10,000", "PO-3391", "2024-05-01"),
    Triplet("po-3391 widget line total", "amount", "$12,000", "Invoice INV-8842", "2024-06-03"),
    Triplet("acme order tax", "amount", "$1,000", "Contract ACME-2023", "2023-01-15"),
    Triplet("acme order tax", "amount", "$1,900", "Invoice INV-9001", "2024-07-10"),
]

EXPECTED_TOTAL = 5300.0

DOCS = [
    {"id": "Contract ACME-2023", "timestamp": "2023-01-15",
     "text": "Master agreement with ACME. Early-payment credit due to buyer: $2,400 "
             "if invoices are paid within 10 days. Sales tax on the order: $1,000 (10%)."},
    {"id": "PO-3391", "timestamp": "2024-05-01",
     "text": "Purchase order PO-3391. Widgets line total: $10,000 for 100 units."},
    {"id": "Invoice INV-8842", "timestamp": "2024-06-03",
     "text": "Invoice INV-8842 from ACME. Widgets line total: $12,000. "
             "Early-payment credit applied: $0."},
    {"id": "Invoice INV-9001", "timestamp": "2024-07-10",
     "text": "Invoice INV-9001 from ACME. Sales tax charged: $1,900."},
]
