"""Faithful claim extraction: raw source text -> Triplets with provenance.

cognee's knowledge graph flattens quantitative claims — a small local model
turns "50,000 requests per second" into a generic `requests per second` node and
merges the same entity across sources, so the conflicting values never survive to
the contradiction engine. This module extracts claims directly from each source's
raw text instead, preserving the numeric object and attaching source id + time.

The LLM call is injectable (`extractor`) so the pipeline is unit-testable offline
with no model, mirroring `contradictions.default_llm_judge`.
"""
from crosscheck.model import Triplet


def _norm(s):
    """Normalize subject/predicate so the structural pre-filter groups matching
    claims across sources (case/spacing differ between model outputs)."""
    return " ".join(str(s).strip().lower().split())


def extract_claims(sources, extractor=None):
    """sources: list of {id, timestamp, text} -> list[Triplet].

    Each source is turned into atomic (subject, predicate, object) claims tagged
    with the source id and timestamp. subject/predicate are normalized; object
    (which carries the value, e.g. "50,000 requests per second") is kept verbatim.
    """
    extractor = extractor or default_llm_extract
    out = []
    for s in sources:
        for claim in extractor(s["text"]):
            subject = _norm(claim.get("subject"))
            predicate = _norm(claim.get("predicate"))
            obj = str(claim.get("object", "")).strip()
            if not subject or not predicate or not obj:
                continue
            out.append(
                Triplet(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    source=s.get("id", "unknown"),
                    timestamp=s.get("timestamp", ""),
                )
            )
    return out


def default_llm_extract(text):
    """Extract atomic claims from one source's text via cognee's LLM gateway.

    Returns a list of {subject, predicate, object} dicts. Kept deliberately flat
    — a single number is easy for a weak local model, unlike a full KG schema.
    """
    import asyncio
    from typing import List

    from pydantic import BaseModel, Field
    from cognee.infrastructure.llm.LLMGateway import LLMGateway

    class Claim(BaseModel):
        subject: str = Field(description="the entity the claim is about, e.g. 'FooDB'")
        predicate: str = Field(
            description="short lowercase attribute, e.g. 'throughput', 'license', 'language'"
        )
        object: str = Field(
            description="the value, kept verbatim including numbers and units, "
            "e.g. '50,000 requests per second'"
        )

    class ClaimList(BaseModel):
        claims: List[Claim]

    system_prompt = (
        "Extract every atomic factual claim as (subject, predicate, object). "
        "Use a consistent short lowercase predicate for the same kind of attribute "
        "across texts (e.g. always 'throughput'). Keep numbers and units verbatim "
        "in the object. Do not infer or merge; one claim per fact."
    )
    result = asyncio.run(
        LLMGateway.acreate_structured_output(
            text_input=text,
            system_prompt=system_prompt,
            response_model=ClaimList,
        )
    )
    return [c.model_dump() for c in result.claims]
