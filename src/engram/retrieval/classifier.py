"""Query classification — rule-based heuristic for retrieval weight assignment."""

from __future__ import annotations

from engram.types import QueryType, RetrievalWeights

TEMPORAL_SIGNALS = [
    "when", "last time", "recently", "before", "after",
    "yesterday", "last week", "first time", "history", "ago",
    "earlier", "previously",
]

FACTUAL_SIGNALS = [
    "what is", "who is", "where does", "email", "name",
    "address", "phone", "role", "title", "how many",
    "which", "tell me about",
]

PREFERENCE_SIGNALS = [
    "prefer", "like", "favorite", "opinion", "think about",
    "feel about", "style", "approach", "choice", "rather",
]

GLOBAL_SIGNALS = [
    "overview", "summary", "themes", "all about",
    "everything about", "big picture", "high level",
    "main topics", "key entities", "what do you know",
]


def classify_query(query: str) -> tuple[RetrievalWeights, QueryType]:
    """Rule-based query classification. Returns retrieval weights and query type."""
    q = query.lower()

    if any(signal in q for signal in GLOBAL_SIGNALS):
        return (
            RetrievalWeights(vector=0.10, graph=0.20, temporal=0.10),
            QueryType.GLOBAL,
        )

    if any(signal in q for signal in TEMPORAL_SIGNALS):
        return (
            RetrievalWeights(vector=0.20, graph=0.30, temporal=0.50),
            QueryType.TEMPORAL,
        )

    if any(signal in q for signal in FACTUAL_SIGNALS):
        return (
            RetrievalWeights(vector=0.20, graph=0.60, temporal=0.20),
            QueryType.FACTUAL,
        )

    if any(signal in q for signal in PREFERENCE_SIGNALS):
        return (
            RetrievalWeights(vector=0.50, graph=0.30, temporal=0.20),
            QueryType.PREFERENCE,
        )

    # Default balanced
    return (
        RetrievalWeights(vector=0.35, graph=0.40, temporal=0.25),
        QueryType.DEFAULT,
    )
