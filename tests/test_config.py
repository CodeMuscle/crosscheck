import os
import pytest
from crosscheck import config


def test_dataset_constant():
    assert config.DATASET == "research"


def test_require_llm_key_raises_when_unset(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        config.require_llm_key()


def test_require_llm_key_returns_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    assert config.require_llm_key() == "sk-test"
