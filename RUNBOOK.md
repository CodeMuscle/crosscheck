# RUNBOOK

## Start
1. `export LLM_API_KEY=sk-...`
2. Start cognee's graph viz server on :8000:
   `python -c "import asyncio, cognee; asyncio.run(cognee.start_visualization_server(port=8000))"`
3. Start Crosscheck API on :8010:
   `uvicorn crosscheck.api:app --port 8010`
4. Open http://localhost:8010

## 2-minute demo
1. Click **Ingest** (empty box → loads preset pack). Graph grows.
2. **Ask**: "What is FooDB's throughput?" → cited answer.
3. Click **Refresh** under Contradictions → 🚨 FooDB 50k (2021) vs 10k (2024).
4. Toggle **live**, enter a topic → graph expands (gap-filling).
5. Restart the API; re-open → contradictions still there (persistence).
