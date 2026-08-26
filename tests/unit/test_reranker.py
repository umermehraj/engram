"""Tests for optional cross-encoder reranker."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engram.config import EngramConfig
from engram.retrieval.reranker import Reranker
from engram.types import Entity


@pytest.fixture
def config() -> EngramConfig:
    return EngramConfig(reranker_model="mock-reranker", reranker_top_k=3)


@pytest.fixture
def mock_graph() -> MagicMock:
    graph = MagicMock()
    graph.get_entity = AsyncMock()
    graph.get_active_relationships = AsyncMock(return_value=[])
    return graph


def _entity(entity_id: str, summary: str) -> Entity:
    return Entity(
        id=entity_id,
        tenant_id="default",
        user_id="test",
        name=entity_id,
        entity_type="concept",
        summary=summary,
    )


async def test_reranker_reorders_candidates(config, mock_graph):
    reranker = Reranker(config)

    mock_graph.get_entity.side_effect = [
        _entity("a", "Alpha entity"),
        _entity("b", "Beta entity"),
        _entity("c", "Charlie entity"),
    ]

    # Mock CrossEncoder to score in reverse order
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.1, 0.9, 0.5]

    with patch.object(reranker, "_get_model", new_callable=AsyncMock, return_value=mock_model):
        candidates = [("a", 1.0), ("b", 0.5), ("c", 0.3)]
        result = await reranker.rerank("test query", candidates, mock_graph)

    # b scored highest (0.9), then c (0.5), then a (0.1)
    assert result[0][0] == "b"
    assert result[1][0] == "c"
    assert result[2][0] == "a"


async def test_reranker_handles_empty_candidates(config, mock_graph):
    reranker = Reranker(config)
    result = await reranker.rerank("test", [], mock_graph)
    assert result == []


async def test_reranker_skips_entities_without_summary(config, mock_graph):
    reranker = Reranker(config)

    mock_graph.get_entity.side_effect = [
        _entity("a", ""),  # empty summary
        _entity("b", "Has a summary"),
    ]

    mock_model = MagicMock()
    mock_model.predict.return_value = [0.8]

    with patch.object(reranker, "_get_model", new_callable=AsyncMock, return_value=mock_model):
        candidates = [("a", 1.0), ("b", 0.5)]
        result = await reranker.rerank("test", candidates, mock_graph)

    # Only b was reranked (a had empty summary)
    assert result[0][0] == "b"
    assert result[1][0] == "a"  # appended from remaining


async def test_reranker_appends_unreranked_candidates(config, mock_graph):
    config.reranker_top_k = 1  # Only rerank the first candidate
    reranker = Reranker(config)

    mock_graph.get_entity.side_effect = [
        _entity("a", "Alpha"),
    ]

    mock_model = MagicMock()
    mock_model.predict.return_value = [0.5]

    with patch.object(reranker, "_get_model", new_callable=AsyncMock, return_value=mock_model):
        candidates = [("a", 1.0), ("b", 0.8), ("c", 0.6)]
        result = await reranker.rerank("test", candidates, mock_graph)

    # a reranked, b and c appended in original order
    assert len(result) == 3
    assert result[0][0] == "a"
    assert result[1][0] == "b"
    assert result[2][0] == "c"


async def test_reranker_respects_top_k(config, mock_graph):
    reranker = Reranker(config)

    mock_graph.get_entity.side_effect = [
        _entity("a", "Alpha"),
        _entity("b", "Beta"),
        _entity("c", "Charlie"),
    ]

    mock_model = MagicMock()
    mock_model.predict.return_value = [0.9, 0.5, 0.1]

    with patch.object(reranker, "_get_model", new_callable=AsyncMock, return_value=mock_model):
        candidates = [("a", 1.0), ("b", 0.5), ("c", 0.3)]
        result = await reranker.rerank("test", candidates, mock_graph, top_k=2)

    assert len(result) == 2


async def test_reranker_returns_original_when_no_summaries(config, mock_graph):
    reranker = Reranker(config)

    mock_graph.get_entity.side_effect = [
        None,  # entity not found
        _entity("b", ""),  # empty summary
    ]

    candidates = [("a", 1.0), ("b", 0.5)]
    result = await reranker.rerank("test", candidates, mock_graph)

    # Falls back to original order since no valid pairs
    assert result == candidates
