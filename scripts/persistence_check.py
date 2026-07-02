"""Prove cross-session memory: ingest once, then a fresh process re-queries from the store."""
import sys

from crosscheck.ingest import current_graph
from crosscheck.graph_access import triplets_from_graph

nodes, edges = current_graph()
tri = triplets_from_graph(nodes, edges)
foodb = [t for t in tri if t.subject == "FooDB"]
if not foodb:
    print("FAIL: no FooDB claims found in the persisted graph — was the preset ingested?")
    sys.exit(1)
print(f"OK: {len(foodb)} FooDB claims served from the store without re-ingesting.")
