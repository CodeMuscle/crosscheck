from dataclasses import dataclass


@dataclass(frozen=True)
class Triplet:
    subject: str
    predicate: str
    object: str
    source: str
    timestamp: str


@dataclass(frozen=True)
class CandidatePair:
    subject: str
    predicate: str
    a: Triplet
    b: Triplet


@dataclass(frozen=True)
class Contradiction:
    entity: str
    claim_a: str
    source_a: str
    time_a: str
    claim_b: str
    source_b: str
    time_b: str
    explanation: str
