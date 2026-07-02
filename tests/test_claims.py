"""Offline: claim extraction -> contradiction, with an injected fake extractor."""
from crosscheck.claims import extract_claims
from crosscheck.contradictions import find_contradictions

SOURCES = [
    {"id": "srcA-2021", "timestamp": "2021-03-01",
     "text": "FooDB sustained 50,000 requests per second."},
    {"id": "srcD-2024", "timestamp": "2024-09-01",
     "text": "FooDB sustained 10,000 requests per second."},
]


def _fake_extractor(text):
    # deterministic stand-in for the LLM: pull the throughput value from the text
    value = "50,000 requests per second" if "50,000" in text else "10,000 requests per second"
    return [{"subject": "FooDB", "predicate": "Throughput", "object": value}]


def test_extract_normalizes_and_tags_provenance():
    triplets = extract_claims(SOURCES, extractor=_fake_extractor)
    assert len(triplets) == 2
    # subject/predicate normalized so the two sources group together
    assert {t.subject for t in triplets} == {"foodb"}
    assert {t.predicate for t in triplets} == {"throughput"}
    # object kept verbatim, provenance attached
    assert {t.source for t in triplets} == {"srcA-2021", "srcD-2024"}
    assert any("50,000" in t.object for t in triplets)


def test_contradiction_fires_on_extracted_claims():
    triplets = extract_claims(SOURCES, extractor=_fake_extractor)
    found = find_contradictions(triplets, judge=lambda p: (True, "different throughput values"))
    assert len(found) == 1
    c = found[0]
    assert c.entity == "foodb"
    assert {c.source_a, c.source_b} == {"srcA-2021", "srcD-2024"}


def test_blank_fields_skipped():
    triplets = extract_claims(
        [{"id": "s", "timestamp": "", "text": "x"}],
        extractor=lambda _t: [{"subject": "", "predicate": "p", "object": "o"}],
    )
    assert triplets == []
