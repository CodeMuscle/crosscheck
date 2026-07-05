# Argus — Spend/Contract Leakage Auditor

**Date:** 2026-07-05
**Status:** Approved design
**Built on:** Crosscheck contradiction engine (reused untouched)

## Problem

Enterprises lose 1–3% of spend to billing errors and unenforced contract terms:
discounts that were negotiated but never applied, invoices that don't match the
purchase order, invoice totals that don't add up. These are hidden in a pile of
contracts, POs, and invoices that no human cross-checks line by line.

## Insight (why this is nearly free to build)

A contract line and an invoice line are **the same fact with two different
values** — exactly what Crosscheck already detects. Contract: "early-pay credit
due $2,400." Invoice: "credit applied $0." The existing engine flags it. Argus
adds **one** thing: a **dollar figure** on each contradiction, turning "sources
disagree" into "**$2,400 you're losing**."

## Non-invasive guarantee

Argus is a **new `argus/` package + its own endpoint + its own static panel**.
It imports and reuses — but does not modify — `crosscheck/claims.py`,
`crosscheck/contradictions.py`, cognee storage, and the FastAPI/panel patterns.
The existing Crosscheck app, its model, and its tests are untouched.

## Architecture — 4 units (only one is new logic)

### 1. `argus/preset.py` (data)
~7 short finance docs as text (2 contracts, 2 POs, 3 invoices) with **3 planted
leakage cases**, all expressed as *dollar-denominated numeric contradictions* so
impact is a clean subtraction:

| Case | Source A (claim) | Source B (claim) | $ impact |
|---|---|---|---|
| A. Discount not applied | Contract ACME-2023: "early-pay credit due **$2,400**" | Invoice INV-8842: "credit applied **$0**" | $2,400 |
| B. PO vs invoice price | PO-3391: "line total **$10,000**" | Invoice INV-8842: "line total **$12,000**" | $2,000 |
| C. Tax overbill | Contract ACME-2023: "tax due **$1,000** (10%)" | Invoice INV-9001: "tax charged **$1,900**" | $900 |

Headline total: **$5,300**. Each case shares a `subject` across its two sources
so the existing structural grouping performs the contract↔invoice join for free.

`preset.py` exposes `DOCS` (raw text, for the graph/story) and `PRESET_CLAIMS`
(pre-extracted faithful claims). **Demo-safety:** like Crosscheck's existing
`_claims_cache`, the demo path uses `PRESET_CLAIMS` so it's deterministic on a
weak local model; live extraction via reused `extract_claims` stays available.

### 2. claims (reuse)
`crosscheck.claims.extract_claims(sources)` → `(subject, predicate, object,
source_id, timestamp)`. Terms are framed as claims (`subject="ACME early-pay
credit"`, `predicate="amount"`, `object="$2,400"`). No change to the module.

### 3. `argus/impact.py` (NEW — the only new logic, ~40 lines)
```
dollar_impact(contradiction) -> {"amount": float|None, "category": str, "direction": str}
```
Deterministic, no LLM:
- Parse a money value from each of `claim_a` / `claim_b` (regex `$` + digits).
- `amount = abs(a - b)`; `direction` = overbilled/undercredited by sign.
- `category` by keyword in `entity`/`predicate`: "credit"/"discount" →
  *"Discount not applied"*; "line total"/"PO"/"price" → *"Price mismatch"*;
  "tax" → *"Tax overbill"*; else *"Amount mismatch"*.
- Non-money values → `amount=None` (finding shown as "needs review", not $).

Offline unit test asserts all 3 preset cases produce the expected $ and category.

### 4. `argus/api.py` + `argus/static/index.html` (thin)
- `GET /leakage` → `{total_at_risk, findings:[{...contradiction, amount, category}]}`,
  findings sorted by `amount` desc.
- Flow: `PRESET_CLAIMS → find_contradictions → dollar_impact per finding → rank`.
- Panel: headline **"$X in leakage found across N invoices"** + one card per
  finding (Source A vs Source B, category badge, **$ impact**, sources + dates).
  Reuses Crosscheck's panel CSS.
- Runs as its own app (`uvicorn argus.api:app --port 8020`), separate from
  Crosscheck on :8010.

## Data flow
`preset docs → (PRESET_CLAIMS | extract_claims) → find_contradictions →
dollar_impact → rank by $ → /leakage → panel headline + cards`

## Testing
- `tests/test_impact.py` (offline, no LLM): each preset case → correct $ + category;
  non-money contradiction → `amount=None`; ranking is descending.
- One live smoke (`argus/live_smoke.py`): preset → contradictions → total $ printed.

## Out of scope (YAGNI backlog — deferred, tracked to revisit)
1. File/PDF/CSV upload + OCR (+2–3h).
2. Live-ingest of pasted real docs (+45m — best first add-on).
3. Multi-currency (+20m; demo is USD).
4. Rules engine for $ impact instead of the heuristic (+1–2h).

## Build order (~2h)
1. `preset.py` (docs + PRESET_CLAIMS + expected cases) — 25m
2. `impact.py` + `test_impact.py` — 30m
3. `api.py` `/leakage` — 20m
4. `static/index.html` panel — 30m
5. live smoke + fixes + screenshot — 25m
