"""Contradiction detection: structural pre-filter (B) + LLM-judge confirm (A)."""
from itertools import combinations

from crosscheck.model import CandidatePair, Contradiction


def structural_candidates(triplets):
    """Pairs sharing (subject, predicate) but with different object AND different source."""
    groups = {}
    for t in triplets:
        groups.setdefault((t.subject, t.predicate), []).append(t)
    candidates = []
    for (subject, predicate), members in groups.items():
        for a, b in combinations(members, 2):
            if a.object != b.object and a.source != b.source:
                candidates.append(CandidatePair(subject=subject, predicate=predicate, a=a, b=b))
    return candidates


def judge_candidates(pairs, judge):
    """Confirm candidates with an injected judge callable -> (is_conflict, explanation)."""
    out = []
    for pair in pairs:
        is_conflict, explanation = judge(pair)
        if is_conflict:
            out.append(
                Contradiction(
                    entity=pair.subject,
                    claim_a=pair.a.object, source_a=pair.a.source, time_a=pair.a.timestamp,
                    claim_b=pair.b.object, source_b=pair.b.source, time_b=pair.b.timestamp,
                    explanation=explanation,
                )
            )
    return out


def default_llm_judge(pair):
    """Ask the LLM whether two sourced claims about the same entity conflict."""
    import asyncio

    from cognee.infrastructure.llm.LLMGateway import LLMGateway

    prompt = (
        f"Two sources make claims about '{pair.subject}' ({pair.predicate}).\n"
        f"Source A ({pair.a.source}): {pair.a.object}\n"
        f"Source B ({pair.b.source}): {pair.b.object}\n"
        "Do these directly contradict each other (cannot both be true)? "
        "Answer strictly 'YES: <reason>' or 'NO: <reason>'."
    )
    reply = asyncio.run(
        LLMGateway.acreate_structured_output(
            text_input=prompt,
            system_prompt="You judge whether two claims contradict. Be strict.",
            response_model=str,
        )
    )
    is_conflict = reply.strip().upper().startswith("YES")
    explanation = reply.split(":", 1)[-1].strip() if ":" in reply else reply.strip()
    return is_conflict, explanation


def find_contradictions(triplets, judge=None):
    judge = judge or default_llm_judge
    return judge_candidates(structural_candidates(triplets), judge)
