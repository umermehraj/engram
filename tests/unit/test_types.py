"""Tests for Pydantic data models."""

import pytest
from pydantic import ValidationError

from engram.types import (
    Entity,
    Relationship,
    RelType,
    RetrievalWeights,
    Fact,
    MemoryContext,
)


def test_entity_defaults():
    e = Entity(tenant_id="t1", user_id="u1", name="FastAPI", entity_type="tool")
    assert e.id.startswith("ent_")
    assert e.confidence == 1.0
    assert e.embedding is None
    assert e.metadata == {}


def test_entity_confidence_bounds():
    with pytest.raises(ValidationError):
        Entity(tenant_id="t1", user_id="u1", name="x", entity_type="tool", confidence=1.5)
    with pytest.raises(ValidationError):
        Entity(tenant_id="t1", user_id="u1", name="x", entity_type="tool", confidence=-0.1)


def test_relationship_is_active():
    r = Relationship(
        from_entity_id="a", to_entity_id="b", rel_type=RelType.DECIDED
    )
    assert r.is_active is True

    from datetime import datetime
    r2 = Relationship(
        from_entity_id="a", to_entity_id="b", rel_type=RelType.DECIDED,
        invalid_from=datetime.utcnow(),
    )
    assert r2.is_active is False


def test_rel_type_enum():
    assert RelType.DECIDED.value == "decided"
    assert RelType("prefers") == RelType.PREFERS


def test_retrieval_weights_defaults():
    w = RetrievalWeights()
    assert w.vector == 0.35
    assert w.graph == 0.40
    assert w.temporal == 0.25


def test_fact_model():
    f = Fact(subject="user", predicate="decided", object="FastAPI")
    assert f.confidence == 1.0
    assert f.is_update is False


def test_memory_context_empty():
    ctx = MemoryContext()
    assert ctx.text == ""
    assert ctx.blocks == []
    assert ctx.total_tokens == 0
