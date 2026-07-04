# Distribution — where to post + copy

## Where

- **Blog body** (`docs/blog.md`): host on **dev.to** or **Hashnode** (devs, code
  blocks render, canonical-URL friendly). Cross-post canonical to your own site
  if you have one.
- **X**: the thread below. Tag the cognee account, add the 20s hero clip as the
  first-tweet video (video-first tweets get far more reach).
- **LinkedIn**: the single post below + the full 2-min video native-uploaded
  (don't just link YouTube — native video ranks higher).
- **Hackathon**: submit repo + video where the cognee "Hangover" hackathon
  collects entries (Discord / submission form). This is the primary target.
- **Optional**: Show HN ("Show HN: Crosscheck – a research copilot that catches
  its sources contradicting each other, runs on local Llama"). Only if the repo
  README + demo are polished; HN is unforgiving.

Post order: blog first (gets a URL) → X thread + LinkedIn link to it → hackathon
submission → HN last.

---

## X thread

**1/**
Most AI research tools have two blind spots: they forget between sessions, and
they never notice when two of your sources flatly contradict each other.

I built Crosscheck to fix both — on cognee, running fully offline on a local
Llama. 🧵

[attach 20s hero clip]

**2/**
The demo: feed it three dated benchmark reports on a database, "FooDB."

Ask a question → you get a cited answer from a knowledge graph.

Hit refresh → 🚨 "50,000 req/s (2021) vs 10,000 req/s (2024) — can't both be
true." It names both sources and explains the conflict.

**3/**
The obvious design is a pure graph query: build the KG, find the same
attribute with different values.

It breaks on a small local model. The extractor turns "50,000 req/s" into a
generic node — the number is *gone* — and merges the entity across sources.

**4/**
Fix: fan the sources out twice.

→ into cognee for storage, the graph, and cited search
→ into a thin claim extractor that keeps the value verbatim with its source

Then a structural pre-filter + an LLM judge decide what actually contradicts.

**5/**
Getting cognee to run at all on llama3.1:8b took three switches: BAML for
tolerant JSON parsing, neutering a summarization step small models can't
satisfy, and turning off multi-user graph scoping.

All env-driven. OpenAI/Gemini are drop-in.

**6/**
Runs on Ollama, no API key. Contradiction detection, cited memory, and a gap
finder that tells you what to research next.

Code + write-up: https://github.com/CodeMuscle/crosscheck
Built on @cognee_ ‍

---

## LinkedIn post

I built an AI research copilot that catches its own sources lying — and it runs
fully offline on a local Llama.

Two things most research tools get wrong: they forget everything between
sessions, and they never flag when two sources disagree. Crosscheck, built on
cognee, does both.

Feed it three dated benchmark reports on a database. Ask a question and you get
an answer that cites its sources. Then it flags the contradiction: one report
says 50,000 requests/second in 2021, another says 10,000 in 2024 — it names both
sources, the dates, and why they can't both be true.

The interesting part was what didn't work. The clean design — build a knowledge
graph, query for conflicting values — falls apart on a small local model: it
drops the numbers during extraction and merges the entity across sources, so
there's nothing left to compare. The fix was to pull faithful claims straight
from the source text, keep each value with its provenance, and run a cheap
structural pre-filter before an LLM judge confirms the conflict. cognee still
does the storage, the graph visualization, and cited retrieval.

Fully offline on Ollama, with OpenAI/Gemini as a drop-in. Code and a 2-minute
demo below.

https://github.com/CodeMuscle/crosscheck · Built on cognee

#AI #KnowledgeGraphs #LLM #opensource #cognee
