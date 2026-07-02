# Building an AI research copilot that catches its sources lying

Research tools forget across sessions, and they never notice when two sources
disagree. Crosscheck is a small copilot on top of [cognee](https://cognee.ai)
that does both: persistent memory of everything you feed it, and a hero feature
that flags when sources contradict each other — e.g. "FooDB sustained 50,000
req/s" (2021) vs "only 10,000 req/s" (2024).

## The obvious design — and why it wasn't enough

The first instinct is to make contradiction detection a pure graph query: build
cognee's knowledge graph, then look for the same entity+attribute with different
values across sources. Elegant, but it breaks on a real local stack (llama3.1:8b
via Ollama). Two failures show up:

1. **The knowledge graph flattens quantities.** The extractor turns "50,000
   requests per second" into a generic `requests per second` node and drops the
   number. The conflicting values never make it into the graph.
2. **Entities get merged across sources.** Every mention of FooDB collapses to
   one node, so the two throughput claims dedup into a single edge — nothing left
   to compare.

So the graph is great for storage, visualization, and cited retrieval, but it
can't be the *source of truth* for a quantitative contradiction.

## The fix: extract faithful claims, judge them structurally

Crosscheck reads claims straight from each source's raw text — a thin, flat
`(subject, predicate, object)` extraction that keeps the number verbatim and
tags it with the source id and timestamp. Extracting one value is easy even for a
small local model, unlike a full graph schema. Then a two-stage engine:

- **Structural pre-filter:** group claims by normalized (subject, predicate);
  flag pairs with the same key, different value, different source.
- **LLM judge:** confirm each candidate actually contradicts ("cannot both be
  true"), with the reason.

On the FooDB pack this fires exactly once: 50k (2021) vs 10k (2024), confirmed.

## Making cognee survive a weak local model

Getting the graph to build at all on llama3.1:8b took three settings, all in
`.env.example`: switch cognee's structured-output framework to **BAML** (its
schema-aligned parsing tolerates loose JSON), neutralize the fragile chunk
**summarization** task (which small models can't satisfy and which Crosscheck
doesn't use), and turn off **multi-user access control** so a direct graph read
sees the whole store.

## Self-improving

A thin gap finder ranks sparsely-connected nodes and asks the LLM for the next
research question — so the copilot tells you what it's missing. Everything
persists in cognee's stores, so a fresh process re-answers without re-ingesting.

Runs fully offline on Ollama; an OpenAI or Gemini key is a drop-in alternative.

Repo + 2-min video: (link)
