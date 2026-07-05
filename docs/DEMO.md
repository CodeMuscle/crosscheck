# Crosscheck — 2-Minute Demo Script

A self-improving research copilot on [cognee](https://cognee.ai): persistent
memory + a hero feature that flags when sources contradict each other.

## Setup (before recording)

1. Ollama running with the two models: `ollama pull llama3.1:8b` and
   `ollama pull nomic-embed-text`.
2. From the repo root:
   ```bash
   set -a && source .env && set +a
   source .venv/bin/activate
   uvicorn serve:app --port 8000        # hub: /crosscheck/ + /argus/
   ```
3. Open **http://localhost:8000/crosscheck/** (Argus is at `/argus/`). The graph viz is served in-app at `/crosscheck/graph`.

The FooDB demo pack is already ingested and **persists across restarts**, so the
graph and the contradiction card load immediately — no waiting on camera.

---

## The script (data already persisted — leads with the hero)

**1. Open the app — pause on the graph** (~15s)
> "This is Crosscheck's live memory — 20 nodes, 36 edges. It persisted across a
> restart; nothing was re-ingested."

Point out the Story/Type layout: sources `srcA-2021` and `srcD-2024` both wire
into the `foodb` and `metric` nodes — the contradiction is visible in the graph.

**2. Contradictions (§3) — the hero** (~40s)
The 🚨 card is already showing:
> **foodb** — srcA-2021 (2021-03-01): **50,000 requests per second**
> vs srcD-2024 (2024-09-01): **10,000 requests per second**
> *"…same metric and time frame, but different values."*

> "The hero: it caught two sources disagreeing on FooDB's throughput — who said
> what, and when. Claims are extracted straight from the source text (keeping the
> number + its origin), then a structural pre-filter and an LLM judge confirm the
> pair can't both be true."

Optional: click the **…** refresh to show it recomputing live.

**3. Gaps to research (§4) — the self-improving loop** (~30s)
Click **Suggest**. Grounded questions appear:
> "It ranks the sparsely-connected nodes and asks what to research next —
> database performance, MIT vs copyleft licensing, throughput metrics."

**4. Graph — live cognee memory** (~20s)
Drag a node; switch the **Graph / Schema / Memory** tabs at the top.
> "All of this is real cognee memory — storage, the knowledge graph, and cited
> retrieval, running fully offline on a local Llama."

---

## Cautions for the recording

- **Skip Ask (§2) on camera.** `/ask` is flaky on a small local model
  (cognee's search-completion path uses a `str | None` field BAML can't map on
  llama3.1:8b). It works on a hosted model; the demo leads with Contradictions.
- **Gaps' 5th question** can drift off-topic (a cognee KG over-extracted a
  spurious concept node whose neighbours are noise). Stop at 4 or scroll past it.
- Google Fonts / favicon 404 console warnings are cosmetic (offline font
  fallback); they don't affect anything on screen.

---

## Alternative: film the "empty → Ingest → graph grows" narrative

Stronger story, but ~2-3 min of live cognify on Ollama with some on-camera risk.
Reset first (prune the store), then start from step 1 of the in-app onboarding:
Ingest the demo pack → watch the graph populate → Contradictions → Gaps.

## Why the architecture (30s of narration if asked)

cognee's knowledge graph can't be the source of truth for a quantitative
contradiction on a weak local model: the extractor flattens "50,000 requests per
second" into a generic node and merges entities across sources, so the
conflicting numbers never survive into the graph. Crosscheck reads faithful
`(subject, predicate, object)` claims from raw text instead — verbatim number +
source id + timestamp — and feeds those to the structural + judge pipeline.
cognee still powers storage, graph visualization, and cited search.
