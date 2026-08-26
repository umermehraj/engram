"""Tests for RRF fusion."""

from engram.retrieval.fusion import fuse_candidates
from engram.types import RetrievalWeights, ScoredNode


def test_single_source():
    vector = [ScoredNode(node_id="a", score=1.0, source="vector")]
    result = fuse_candidates(vector, [], [], RetrievalWeights())
    assert len(result) == 1
    assert result[0][0] == "a"
    assert result[0][1] > 0


def test_multi_source_bonus():
    node_a_vec = ScoredNode(node_id="a", score=1.0, source="vector")
    node_a_graph = ScoredNode(node_id="a", score=1.0, source="graph")

    result_multi = fuse_candidates([node_a_vec], [node_a_graph], [], RetrievalWeights())
    result_single = fuse_candidates([node_a_vec], [], [], RetrievalWeights())

    # Multi-source score should be higher
    assert result_multi[0][1] > result_single[0][1]


def test_ranking_order():
    vector = [
        ScoredNode(node_id="a", score=1.0, source="vector"),
        ScoredNode(node_id="b", score=0.5, source="vector"),
    ]
    graph = [
        ScoredNode(node_id="a", score=0.8, source="graph"),
        ScoredNode(node_id="c", score=0.9, source="graph"),
    ]
    result = fuse_candidates(vector, graph, [], RetrievalWeights())

    # "a" appears in both sources — should be ranked first
    assert result[0][0] == "a"


def test_empty_inputs():
    result = fuse_candidates([], [], [], RetrievalWeights())
    assert result == []
