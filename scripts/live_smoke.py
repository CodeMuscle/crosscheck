"""Live end-to-end smoke: prune -> ingest preset -> cognify -> contradictions."""
import asyncio

import cognee
from crosscheck.ingest import ingest, current_graph
from crosscheck.graph_access import triplets_from_graph
from crosscheck.contradictions import find_contradictions
from crosscheck.preset.benchmarks import PRESET


def run(c):
    return asyncio.run(c)


print(">>> pruning old cognee data (clears stale embedding dims)...", flush=True)
run(cognee.prune.prune_data())
run(cognee.prune.prune_system(metadata=True))

print(">>> ingesting preset pack...", flush=True)
print(ingest(PRESET), flush=True)

print(">>> reading graph...", flush=True)
nodes, edges = current_graph()
print(f"nodes={len(nodes)} edges={len(edges)}", flush=True)
for nid, props in nodes[:8]:
    print("  NODE", {k: props.get(k) for k in ("name", "type", "source", "timestamp")}, flush=True)

tri = triplets_from_graph(nodes, edges)
print(f">>> graph triplets (viz/search side): {len(tri)}", flush=True)

# Contradiction hero reads faithful claims extracted from raw text — the cognee
# KG drops numeric values, so it can't feed the contradiction engine directly.
from crosscheck.claims import extract_claims

print(">>> extracting claims from source text...", flush=True)
claims = extract_claims(PRESET)
print(f">>> claims extracted: {len(claims)}", flush=True)
for t in claims:
    print("    CLAIM:", t.subject, "|", t.predicate, "|", t.object, "| src=", t.source, flush=True)

print(">>> finding contradictions...", flush=True)
found = False
for c in find_contradictions(claims):
    found = True
    print("CONTRADICTION:", c.entity, "|", c.claim_a, "vs", c.claim_b, "->", c.explanation, flush=True)
print("DONE found=" + str(found), flush=True)
