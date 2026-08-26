"""Tests for global/thematic search."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from engram.retrieval.global_search import global_search
from engram.retrieval.fusion import fuse_global_candidates
from engram.types import ScoredNode


@pytest.fixture
def mock_graph() -> MagicMock:
    graph = MagicMock()
    graph.execute_cypher = AsyncMock()
    return graph


async def test_global_search_returns_by_degree(mock_graph):
    mock_graph.execute_cypher.return_value = pd.DataFrame({
        "id": ["a", "b", "c"],
        "degree": [10, 5, 1],
    })

    results = await global_search("user1", "default", mock_graph)

    assert len(results) == 3
    assert results[0].node_id == "a"
    assert results[0].score == 1.0  # max degree normalized
    assert results[1].score == 0.5
    assert results[2].score == 0.1
    assert all(r.source == "global" for r in results)


async def test_global_search_empty_graph(mock_graph):
    mock_graph.execute_cypher.return_value = pd.DataFrame(columns=["id", "degree"])

    results = await global_search("user1", "default", mock_graph)
    assert results == []


async def test_global_search_with_type_filter(mock_graph):
    mock_graph.execute_cypher.return_value = pd.DataFrame({
        "id": ["a"],
        "degree": [5],
    })

    results = await global_search(
        "user1", "default", mock_graph, entity_type_filter="person"
    )

    assert len(results) == 1
    # Verify the type filter was passed in the query
    call_args = mock_graph.execute_cypher.call_args
    assert "entity_type" in call_args[0][1]


def test_fuse_global_candidates():
    global_results = [
        ScoredNode(node_id="a", score=1.0, source="global"),
        ScoredNode(node_id="b", score=0.5, source="global"),
    ]
    vector_results = [
        ScoredNode(node_id="b", score=0.9, source="vector"),
        ScoredNode(node_id="c", score=0.8, source="vector"),
    ]

    fused = fuse_global_candidates(global_results, vector_results)

    ids = [nid for nid, _ in fused]
    # b should rank high — it appears in both sources (multi-source bonus)
    assert "b" in ids
    assert "a" in ids
    assert "c" in ids

    # b gets multi-source bonus (1.15x)
    b_score = next(s for nid, s in fused if nid == "b")
    a_score = next(s for nid, s in fused if nid == "a")
    assert b_score > a_score  # b has bonus from appearing in both


def test_fuse_global_empty():
    fused = fuse_global_candidates([], [])
    assert fused == []
