# RUNBOOK

## Setup
1. Copy the env template and pick a profile: `cp .env.example .env`
   - **Default (Profile A):** local Llama via Ollama — free, offline, no key.
     Needs `ollama serve` running and two models:
     `ollama pull llama3.1:8b` and `ollama pull nomic-embed-text`.
   - Can't run local models? Uncomment Profile B (OpenAI) or C (Gemini) in `.env`
     and add your key. (Untested here; the local-Llama path is what we verify.)
2. Install with the BAML extra (required so weak local models don't break cognify):
   `uv pip install -e ".[baml]"`

## Start
1. `set -a && source .env && set +a`
2. Start cognee's graph viz server on :8000:
   `python -c "import asyncio, cognee; asyncio.run(cognee.start_visualization_server(port=8000))"`
3. Start Crosscheck API on :8010:
   `uvicorn crosscheck.api:app --port 8010`
4. Open http://localhost:8010

## Verify the pipeline headless
`python scripts/live_smoke.py` — prunes, ingests the preset, builds the cognee
graph, extracts claims from source text, and prints the 50k-vs-10k contradiction.

## 2-minute demo
1. Click **Ingest** (empty box → loads preset pack). Graph grows.
2. **Ask**: "What is FooDB's throughput?" → cited answer.
3. Click **Refresh** under Contradictions → 🚨 FooDB 50k (2021) vs 10k (2024).
4. Toggle **live**, enter a topic → graph expands (gap-filling).
5. Restart the API; re-open → contradictions still there (persistence).

## Notes
- Contradiction detection reads **claims extracted from raw source text**, not
  the cognee knowledge graph: small local models flatten "50,000 requests per
  second" into a generic node and merge entities across sources, so the
  conflicting numbers never survive into the KG. cognee still powers storage,
  graph visualization, and cited search. See `crosscheck/claims.py`.
