"""Core data types for Engram."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from engram.utils import generate_id


# ── Enums ────────────────────────────────────────────────────────────────────


class RelType(str, Enum):
    """Relationship edge types, ordered by signal strength."""

    # High-signal
    DECIDED = "decided"
    PREFERS = "prefers"
    BELIEVES = "believes"
    WORKS_ON = "works_on"
    REPLACED = "replaced"

    # Medium-signal
    MENTIONED = "mentioned"
    ASKED_ABOUT = "asked_about"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"

    # Meta
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    DERIVED_FROM = "derived_from"


class QueryType(str, Enum):
    TEMPORAL = "temporal"
    FACTUAL = "factual"
    PREFERENCE = "preference"
    GLOBAL = "global"
    DEFAULT = "default"


class EntityType(str, Enum):
    # Abstract entities (extracted from content)
    PERSON = "person"
    PROJECT = "project"
    TOOL = "tool"
    CONCEPT = "concept"
    PREFERENCE = "preference"
    ORGANIZATION = "organization"

    # Data source nodes (the actual ingested artifacts)
    DOCUMENT = "document"
    CONVERSATION = "conversation"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    WEBPAGE = "webpage"
    CODE = "code"


# ── Core Domain Models ───────────────────────────────────────────────────────


class Entity(BaseModel):
    id: str = Field(default_factory=generate_id)
    tenant_id: str
    user_id: str
    name: str
    entity_type: str
    summary: str = ""
    embedding: list[float] | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_referenced_at: datetime = Field(default_factory=datetime.utcnow)
    source_session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    id: str = Field(default_factory=generate_id)
    from_entity_id: str
    to_entity_id: str
    rel_type: RelType
    summary: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    invalid_from: datetime | None = None  # None = still active
    source_session_id: str | None = None
    source_message_idx: int | None = None
    reasoning: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.invalid_from is None


# ── Retrieval Types ──────────────────────────────────────────────────────────


class RetrievalWeights(BaseModel):
    vector: float = 0.35
    graph: float = 0.40
    temporal: float = 0.25


class ScoredNode(BaseModel):
    node_id: str
    score: float
    source: str  # "vector", "graph", "temporal"


class ContextBlock(BaseModel):
    content: str
    node_id: str
    score: float
    timestamp: datetime


class MemoryContext(BaseModel):
    """Result of a memory search — formatted context ready for an LLM prompt."""

    text: str = ""
    blocks: list[ContextBlock] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    total_tokens: int = 0
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)


class Fact(BaseModel):
    """A single extracted fact, used in both ingestion and retrieval responses."""

    id: str = Field(default_factory=generate_id)
    subject: str
    subject_type: str = ""
    predicate: str
    object: str
    object_type: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_update: bool = False
    reasoning: str = ""
    valid_from: datetime | None = None
    source_session_id: str | None = None


# ── Request / Response DTOs ──────────────────────────────────────────────────


class AddMemoryRequest(BaseModel):
    messages: list[dict[str, str]] | None = None
    text: str | None = None
    user_id: str
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AddMemoryResponse(BaseModel):
    entities_created: int = 0
    entities_merged: int = 0
    relationships_created: int = 0
    conflicts_detected: int = 0


class SearchRequest(BaseModel):
    query: str
    user_id: str
    session_id: str | None = None
    top_k: int = 10
    token_budget: int = 4000
    mode: str = "hybrid"  # "hybrid" or "global"
    filters: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    context: str = ""
    facts: list[Fact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryVersion(BaseModel):
    """A single version in a temporal chain."""

    entity_name: str
    relationship_summary: str
    rel_type: str
    valid_from: datetime
    invalid_from: datetime | None = None
    was_active: bool = True
