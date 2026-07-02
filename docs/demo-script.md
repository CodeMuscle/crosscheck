# 2-minute demo — shot list + narration

Total ~120s. Record at 1280×720+, terminal font large. Pre-pull models and
`set -a && source .env && set +a` before recording so nothing stalls on camera.

Pre-roll (not filmed): `ollama serve` running; `python scripts/live_smoke.py`
once to warm caches so the on-camera run is fast.

---

### 0:00–0:15 — Hook (talking head or title card)
> "AI research tools forget everything between sessions, and they never notice
> when two of your sources flatly disagree. Crosscheck, built on cognee, does
> both — and it runs fully offline on a local Llama."

Show: title card → `docs/architecture.md` diagram (2s hold on the diagram).

### 0:15–0:35 — The contradiction, in the UI
Open http://localhost:8010. Click **Ingest** (loads the preset pack); the cognee
graph fills the right pane (served at `/graph`).
> "Three dated benchmark reports about a database called FooDB go in. Watch the
> knowledge graph build."

### 0:35–0:55 — Provenance in the graph
In the embedded graph, point out the **node sets** srcA-2021 / srcB-2022 /
srcD-2024 — every claim is tagged with where and when it came from.
> "Everything is tagged with its source and date — that's the graph working as
> memory, and it's what makes the next part possible."

(The `/ask` cited-answer endpoint works on a hosted model; on a small local model
cognee's search path is flaky, so the local demo leads with the graph. See the
RUNBOOK note.)

### 0:55–1:20 — The hero
Click **Refresh** under Contradictions → the 🚨 card appears.
> "Here's the payoff. One source says 50,000 requests per second in 2021,
> another says 10,000 in 2024. Crosscheck flags it, names both sources and dates,
> and explains why they can't both be true."

Cut to terminal, run `python scripts/live_smoke.py`, scroll to:
```
CLAIM: foodb | throughput | 50,000 requests per second | src= srcA-2021
CLAIM: foodb | throughput | 10,000 requests per second | src= srcD-2024
CONTRADICTION: foodb | 50,000 ... vs 10,000 ... -> same metric, different values
```

### 1:20–1:40 — Why it's not just a graph query (the interesting bit)
Show `crosscheck/claims.py` (the extractor) side by side with the diagram.
> "The graph alone can't do this on a small local model — it drops the numbers
> and merges the entity. So Crosscheck pulls faithful claims straight from the
> text, keeps the value and its source, and runs a structural pre-filter plus an
> LLM judge. cognee still does storage, the graph, and cited search."

### 1:40–1:55 — Self-improving + persistence
Toggle **live**, enter a topic → graph expands. Restart the API, reopen →
contradiction still there.
> "It tells you what it's missing with a gap finder, and everything persists —
> reopen and the memory's intact."

### 1:55–2:00 — Close
> "Runs on Ollama, no API key. Repo and docs in the description."
Show repo URL card.

---

**On-screen code to have open in tabs:** `crosscheck/claims.py`,
`crosscheck/contradictions.py` (the two-stage engine), `docs/architecture.md`.
