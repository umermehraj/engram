"""Weighted Reciprocal Rank Fusion (RRF) across retrieval sources."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from engram.types import RetrievalWeights, ScoredNode


@dataclass
class FusionScore:
    vector: float = 0.0
    graph: float = 0.0
    temporal: float = 0.0
    sources: int = 0


def fuse_candidates(
    vector_results: list[ScoredNode],
    graph_results: list[ScoredNode],
    temporal_results: list[ScoredNode],
    weights: RetrievalWeights,
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    Weighted RRF fusion across three retrieval sources.
    Returns list of (node_id, combined_score) sorted by score descending.
    """
    scores: dict[str, FusionScore] = defaultdict(FusionScore)

    # Rank each source by score descending, then compute RRF
    for rank, node in enumerate(sorted(vector_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].vector = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    for rank, node in enumerate(sorted(graph_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].graph = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    for rank, node in enumerate(sorted(temporal_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].temporal = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    final: list[tuple[str, float]] = []
    for node_id, s in scores.items():
        combined = (
            weights.vector * s.vector
            + weights.graph * s.graph
            + weights.temporal * s.temporal
        )
        # Multi-source bonus: appearing in 2+ retrieval paths = strong signal
        if s.sources >= 2:
            combined *= 1.0 + (0.15 * (s.sources - 1))

        final.append((node_id, combined))

    final.sort(key=lambda x: x[1], reverse=True)
    return final


def fuse_global_candidates(
    global_results: list[ScoredNode],
    vector_results: list[ScoredNode],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Fuse global (degree-based) with vector results for thematic queries."""
    scores: dict[str, FusionScore] = defaultdict(FusionScore)

    for rank, node in enumerate(sorted(global_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].graph = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    for rank, node in enumerate(sorted(vector_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].vector = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    final: list[tuple[str, float]] = []
    for node_id, s in scores.items():
        combined = 0.7 * s.graph + 0.3 * s.vector
        if s.sources >= 2:
            combined *= 1.15
        final.append((node_id, combined))

    final.sort(key=lambda x: x[1], reverse=True)
    return final
