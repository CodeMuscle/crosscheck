# Crosscheck — Design Spec

> A self-improving research copilot that never forgets and catches sources disagreeing.
> Built for the Cognee "Hangover" hackathon (theme: *Build AI that doesn't forget*).
> Date: 2026-07-01.

## One-liner

**"AI research that doesn't forget — and catches itself when sources disagree."**

Crosscheck ingests research sources into a cognee knowledge graph, answers questions
with cited provenance, flags when a new source contradicts stored knowledge, and
inspects its own graph to drive the next round of research. Every headline feature
depends on the *graph* — none of it is reproducible with plain vector recall. This
directly targets the "Best Use of Cognee (depth of memory-API use)" judging criterion.

## Goals

1. Demonstrate graph-native memory: multi-hop, provenance, cross-session persistence.
2. Hero feature: **contradiction detection** across sources (cognee roadmap Approach C+D).
3. Self-improving loop: contradiction-flagging + gap-driven follow-up + persistence.
4. Demoable in ~2 minutes with a deterministic, can't-flake hero moment.
5. Buildable solo in the ~4 remaining hackathon days.

## Non-goals (YAGNI)

- No bespoke React app — reuse cognee's visualization server.
- No custom vector/graph store — use cognee's default SQLite + LanceDB + Ladybug.
- No multi-user auth, no cloud deploy, no billing.
- Gap finder stays intentionally thin (top-N low-degree nodes → questions), not a
  full agentic planner. It is the first scope to cut if time slips.

## Architecture — five focused units

Each unit has one job, a defined interface, and a runnable check.

### 1. Ingestor
- **Input:** a list of URLs / local docs (preset pack) OR a topic string (live web
  search via cognee's `scraping` extra, behind a `--live` toggle).
- **Does:** `cognee.add(source, dataset="research")` → `cognee.cognify(datasets=["research"])`.
  Stamps each source node with provenance metadata: `source_id`, `source_url`,
  `fetched_at` (ISO timestamp), so every downstream claim is traceable.
- **Interface:** `ingest(sources: list[str], live: bool = False) -> IngestResult`.
- **Depends on:** cognee SDK, OpenAI key (for cognify extraction), scraping extra (live only).

### 2. Contradiction engine (hero) — Approach A+B
Two stages, cheap-filter-then-confirm:
- **Structural pre-filter (B):** walk the graph for candidate conflict pairs — claims
  sharing the same subject entity + predicate but arriving from *different sources*
  with *different objects*. Cheap, deterministic, no LLM. Narrows the search space.
- **LLM-judge confirm (A):** for each candidate pair, an LLM judges "do these two
  sourced claims actually contradict?" (guards against legitimately multi-valued
  properties that the structural pass over-flags).
- **Output:** `Contradiction{ entity, claim_a, source_a, time_a, claim_b, source_b,
  time_b, verdict, explanation }`, persisted and surfaced in the alert feed.
- **Interface:** `find_contradictions(dataset="research") -> list[Contradiction]`.

### 3. Gap finder (thin)
- **Does:** rank entity nodes by low degree / dangling references; for the top-N,
  ask an LLM "what's missing about `E`?" → returns next research questions.
- **Loop:** questions can be fed back to the Ingestor (`--live`) to deepen the graph.
- **Interface:** `find_gaps(dataset="research", top_n=5) -> list[ResearchQuestion]`.

### 4. Memory store
- cognee's persistent stores under the `research` dataset (SQLite + LanceDB + Ladybug
  on disk under `DATA_ROOT_DIRECTORY`). Accumulates across sessions.
- Query path prefers stored graph; only the gap finder / live toggle fetch new sources.
- This unit is *configuration + convention*, not new code — it is cognee's default
  persistence, used deliberately.

### 5. API / UI
- Thin **FastAPI** app wrapping the four units, plus cognee's existing graph
  visualization server (reused, not rebuilt).
- Minimal HTML/JS panel with three controls:
  - **Ingest box:** paste URLs / topic + `live` toggle.
  - **Ask box:** → `cognee.search(query, query_type=GRAPH_COMPLETION)` → cited answer.
  - **Contradiction feed:** live list of `Contradiction` alerts; clicking one
    highlights the two nodes in the embedded graph view.

## Data flow

```
ingest(sources)
  → cognee.add → cognee.cognify            (graph grows, provenance stamped)
  → structural pre-filter → LLM-judge      → contradiction feed
  → graph inspect → gap questions          → (optional) auto-research → ingest(...)

ask(question)
  → cognee.search(GRAPH_COMPLETION)         → cited answer (source + timestamp)
```

Every answer and every alert carries provenance pulled from the graph.

## Demo script (~2 min) — engineered so the hero moment can't flake

1. **0:00** Ingest the preset pack — a topic with a *planted, dated contradiction*:
   conflicting reported benchmark numbers for an open-source tool across two dated
   sources (neutral, live-verifiable). Graph grows on screen.
2. **0:30** Ask a question → cited answer straight from the graph.
3. **0:50** 🚨 **CONTRADICTION ALERT**: "Source A (older): X. Source D (newer): not-X."
   Click → the two nodes highlight in the graph. *The shot judges remember.*
4. **1:20** Gap finder: "Graph is thin on Y — researching…" → live search fills it,
   graph visibly expands (self-improving).
5. **1:40** Restart → "it remembers everything; session 2 builds on session 1"
   (persistence).
6. Close on the tagline.

Recorded demo uses the deterministic preset pack; `--live` stays available for
interactive judging on the judges' own topics.

## Tech stack & reuse

- **Language:** Python 3.10+.
- **Core:** cognee SDK (`add`, `cognify`, `search`, persistent stores).
- **API:** FastAPI + uvicorn (thin).
- **Frontend:** minimal HTML/JS embedding cognee's graph visualization (no React build).
- **LLM:** OpenAI (assumed key present) for cognify extraction + the contradiction judge.
- **Live search:** cognee `scraping` extra (Tavily/BeautifulSoup), `--live` only.

We write orchestration + contradiction/gap logic. Infrastructure (stores, graph
extraction, visualization) is cognee's.

## Error handling

- Ingest: a failed fetch/cognify for one source logs and skips; never aborts the batch.
- LLM-judge: on API error, fall back to marking the pair "unconfirmed" (surfaced as a
  weaker structural-only flag) rather than dropping it silently.
- Missing OpenAI key at startup: fail fast with a clear message (cognify can't run).
- Live search off by default so the recorded demo path has no network dependency.

## Testing

One runnable check per non-trivial unit (assert-based, no framework ceremony):
1. **Contradiction engine:** ingest the preset pack containing exactly one planted
   conflict → assert the engine flags exactly that pair (no false positives on the
   multi-valued control claim included in the pack).
2. **Gap finder:** a graph with a deliberately thin node → assert it returns questions
   naming that node.
3. **Persistence:** add a fact, simulate a new session (fresh process, same dataset),
   re-query → assert the fact is served from the store, not re-fetched.

## Build plan (~4 days)

- **Day 1:** Ingestor + cognify + provenance stamping + preset pack. Prove graph builds.
- **Day 2:** Contradiction engine (structural pre-filter → LLM-judge) + its planted-conflict test. The hero.
- **Day 3:** Thin FastAPI + reuse cognee viz + contradiction feed + query panel. Make it demoable.
- **Day 4:** Gap finder (thin) + persistence demo + record 2-min video + write blog/README.
- **Cut-first if time slips:** gap finder. Hero (contradiction) + persistence stand alone.

## Prize alignment

Standalone repo/demo — does **not** touch the 5-merged-PR cap (that cap is only for
PRs merged into cognee). Feeds the flagship hardware prize + blog (Keychron) + social
(swag) + Cognee job-interview tracks. Presentation-quality criterion is served by the
engineered demo + README/blog.

## Open questions / assumptions

- Assumes an OpenAI (or OpenAI-compatible) API key is available for cognify.
- Exact preset-pack sources chosen during Day 1 (neutral dated benchmark claims).
- Project name "Crosscheck" is provisional.
