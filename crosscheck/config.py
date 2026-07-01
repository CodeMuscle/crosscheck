"""Central config: dataset name and LLM key check."""
import os

DATASET = "research"


def require_llm_key() -> str:
    """Return the configured LLM API key, or raise with a clear message."""
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "LLM_API_KEY (or OPENAI_API_KEY) must be set — cognify needs an LLM "
            "to extract the knowledge graph."
        )
    return key
