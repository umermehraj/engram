"""
Engram Demo API
===============
Lightweight FastAPI backend for the portfolio showcase.
Pre-loads sample facts on startup — no API keys needed.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── Engram imports ──────────────────────────────────────────────────────────
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from engram.config import EngramConfig
from engram.ingestion.embedder import Embedder
from engram.ingestion.resolver import EntityResolver
from engram.ingestion.temporal_linker import TemporalLinker
from engram.retrieval.classifier import classify_query
from engram.retrieval.context_assembler import assemble_context
from engram.retrieval.engine import RetrievalEngine
from engram.retrieval.fusion import fuse_candidates
from engram.retrieval.graph_search import graph_search
from engram.retrieval.temporal_search import temporal_search
from engram.retrieval.vector_search import vector_search
from engram.storage.kuzu_backend import KuzuBackend
from engram.storage.lancedb_backend import LanceDBBackend
from engram.storage.metadata_backend import MetadataBackend
from engram.types import Entity, Fact, Relationship, ScoredNode
from engram.utils import generate_id

# ── Sample Data ─────────────────────────────────────────────────────────────

SAMPLE_FACTS = [
    # ── Core project structure (dense hub) ─────────────────────────────────
    Fact(subject="Saalik", subject_type="person", predicate="works_on",
         object="Engram", object_type="project", confidence=0.99,
         reasoning="Building the Engram memory layer"),
    Fact(subject="Alex", subject_type="person", predicate="works_on",
         object="Engram", object_type="project", confidence=0.95,
         reasoning="Frontend engineer on the project"),

    # ── Tech stack decisions with temporal chains ──────────────────────────
    # Backend: Django → FastAPI (temporal supersession — the flagship demo)
    Fact(subject="Saalik", subject_type="person", predicate="decided",
         object="Django", object_type="tool", confidence=0.90,
         reasoning="Initially chose Django for the backend", is_update=False),
    Fact(subject="Saalik", subject_type="person", predicate="replaced",
         object="Django", object_type="tool", confidence=0.95,
         reasoning="Replaced Django with FastAPI for async support"),
    Fact(subject="Saalik", subject_type="person", predicate="decided",
         object="FastAPI", object_type="tool", confidence=0.95,
         reasoning="Chose FastAPI for native async and Pydantic integration"),

    # Database: PostgreSQL → SQLite for local mode (another supersession)
    Fact(subject="Saalik", subject_type="person", predicate="decided",
         object="PostgreSQL", object_type="tool", confidence=0.85,
         reasoning="Initially planned PostgreSQL for all storage"),
    Fact(subject="Saalik", subject_type="person", predicate="replaced",
         object="PostgreSQL", object_type="tool", confidence=0.90,
         reasoning="Replaced PostgreSQL with SQLite for local-first mode"),
    Fact(subject="Saalik", subject_type="person", predicate="decided",
         object="SQLite", object_type="tool", confidence=0.90,
         reasoning="Chose SQLite for zero-config local deployment"),

    # ── Dependency chains (multi-hop traversal) ────────────────────────────
    # Engram → Kuzu → Graph DB → Cypher
    Fact(subject="Engram", subject_type="project", predicate="depends_on",
         object="Kuzu", object_type="tool", confidence=0.95,
         reasoning="Embedded graph database for entity/relationship storage"),
    Fact(subject="Kuzu", subject_type="tool", predicate="related_to",
         object="graph database", object_type="concept", confidence=0.95,
         reasoning="Kuzu is an embedded graph database"),
    Fact(subject="Kuzu", subject_type="tool", predicate="depends_on",
         object="Cypher", object_type="concept", confidence=0.90,
         reasoning="Kuzu uses Cypher query language"),

    # Engram → LanceDB → vector search → ANN
    Fact(subject="Engram", subject_type="project", predicate="depends_on",
         object="LanceDB", object_type="tool", confidence=0.95,
         reasoning="Embedded vector store for similarity search"),
    Fact(subject="LanceDB", subject_type="tool", predicate="related_to",
         object="vector search", object_type="concept", confidence=0.95,
         reasoning="LanceDB provides approximate nearest neighbor search"),
    Fact(subject="vector search", subject_type="concept", predicate="part_of",
         object="hybrid retrieval", object_type="concept", confidence=0.90,
         reasoning="Vector search is one of three retrieval signals"),

    # Engram → FastAPI → Uvicorn → async Python
    Fact(subject="Engram", subject_type="project", predicate="depends_on",
         object="FastAPI", object_type="tool", confidence=0.95,
         reasoning="REST API framework"),
    Fact(subject="FastAPI", subject_type="tool", predicate="depends_on",
         object="Uvicorn", object_type="tool", confidence=0.90,
         reasoning="ASGI server for FastAPI"),
    Fact(subject="FastAPI", subject_type="tool", predicate="related_to",
         object="async Python", object_type="concept", confidence=0.85,
         reasoning="FastAPI is built on async/await"),

    # Engram → sentence-transformers → embeddings
    Fact(subject="Engram", subject_type="project", predicate="depends_on",
         object="sentence-transformers", object_type="tool", confidence=0.95,
         reasoning="Local embedding model for vector search"),
    Fact(subject="sentence-transformers", subject_type="tool", predicate="related_to",
         object="embeddings", object_type="concept", confidence=0.90,
         reasoning="Generates dense vector representations of text"),

    # ── Core concepts (cross-linked) ──────────────────────────────────────
    Fact(subject="hybrid retrieval", subject_type="concept", predicate="part_of",
         object="Engram", object_type="project", confidence=0.95,
         reasoning="Core innovation: fusing vector + graph + temporal signals"),
    Fact(subject="graph database", subject_type="concept", predicate="part_of",
         object="hybrid retrieval", object_type="concept", confidence=0.85,
         reasoning="Graph traversal is one of three retrieval signals"),
    Fact(subject="temporal awareness", subject_type="concept", predicate="part_of",
         object="hybrid retrieval", object_type="concept", confidence=0.85,
         reasoning="Temporal versioning is one of three retrieval signals"),
    Fact(subject="RRF fusion", subject_type="concept", predicate="part_of",
         object="hybrid retrieval", object_type="concept", confidence=0.90,
         reasoning="Reciprocal Rank Fusion combines all three signals"),

    # ── People's preferences and beliefs ──────────────────────────────────
    Fact(subject="Saalik", subject_type="person", predicate="prefers",
         object="Python", object_type="tool", confidence=0.90,
         reasoning="Primary language choice"),
    Fact(subject="Saalik", subject_type="person", predicate="believes",
         object="hybrid retrieval", object_type="concept", confidence=0.88,
         reasoning="Believes hybrid retrieval outperforms single-method approaches"),
    Fact(subject="Saalik", subject_type="person", predicate="prefers",
         object="async Python", object_type="concept", confidence=0.85,
         reasoning="Prefers async patterns for I/O-bound services"),
    Fact(subject="Alex", subject_type="person", predicate="prefers",
         object="TypeScript", object_type="tool", confidence=0.85,
         reasoning="Frontend language of choice"),
    Fact(subject="Alex", subject_type="person", predicate="decided",
         object="React", object_type="tool", confidence=0.90,
         reasoning="Chose React for the demo frontend"),

    # ── Competitor analysis (cross-cluster edges) ─────────────────────────
    Fact(subject="Engram", subject_type="project", predicate="related_to",
         object="Mem0", object_type="tool", confidence=0.70,
         reasoning="Competitor — cloud-only, partial graph support"),
    Fact(subject="Engram", subject_type="project", predicate="related_to",
         object="Zep", object_type="tool", confidence=0.70,
         reasoning="Competitor — has graph but no temporal versioning"),
    Fact(subject="Mem0", subject_type="tool", predicate="related_to",
         object="vector search", object_type="concept", confidence=0.80,
         reasoning="Mem0 uses vector search for retrieval"),
    Fact(subject="Zep", subject_type="tool", predicate="related_to",
         object="graph database", object_type="concept", confidence=0.80,
         reasoning="Zep has knowledge graph capabilities"),

    # ── Data sources linking into the graph ───────────────────────────────
    Fact(subject="Doc: MVP Spec", subject_type="document", predicate="related_to",
         object="Engram", object_type="project", confidence=0.99,
         reasoning="The founding specification document"),
    Fact(subject="Doc: MVP Spec", subject_type="document", predicate="mentioned",
         object="hybrid retrieval", object_type="concept", confidence=0.90,
         reasoning="Spec describes the hybrid retrieval architecture"),
    Fact(subject="Chat: Architecture Review", subject_type="conversation",
         predicate="mentioned", object="Kuzu", object_type="tool", confidence=0.90,
         reasoning="Team discussed Kuzu as the graph backend"),
    Fact(subject="Chat: Architecture Review", subject_type="conversation",
         predicate="mentioned", object="LanceDB", object_type="tool", confidence=0.90,
         reasoning="Team discussed LanceDB as the vector store"),
    Fact(subject="Code: engine.py", subject_type="code", predicate="part_of",
         object="Engram", object_type="project", confidence=0.99,
         reasoning="Core retrieval engine implementation"),
    Fact(subject="Code: engine.py", subject_type="code", predicate="depends_on",
         object="RRF fusion", object_type="concept", confidence=0.90,
         reasoning="Engine implements RRF fusion algorithm"),
]

SCENARIO_FACTS: dict[str, list[Fact]] = {
    "tech_stack": [
        Fact(subject="Alex", subject_type="person", predicate="replaced",
             object="Vue", object_type="tool", confidence=0.90,
             reasoning="Switched from Vue to React for the dashboard"),
        Fact(subject="Alex", subject_type="person", predicate="decided",
             object="Tailwind CSS", object_type="tool", confidence=0.85,
             reasoning="Chose Tailwind for styling"),
        Fact(subject="React", subject_type="tool", predicate="depends_on",
             object="TypeScript", object_type="tool", confidence=0.85,
             reasoning="Using TypeScript with React"),
        Fact(subject="Tailwind CSS", subject_type="tool", predicate="part_of",
             object="Engram", object_type="project", confidence=0.80,
             reasoning="Frontend styling framework"),
    ],
    "deployment": [
        Fact(subject="Saalik", subject_type="person", predicate="decided",
             object="Cloud Run", object_type="tool", confidence=0.90,
             reasoning="Chose Cloud Run for backend deployment"),
        Fact(subject="Saalik", subject_type="person", predicate="decided",
             object="Vercel", object_type="tool", confidence=0.90,
             reasoning="Chose Vercel for frontend hosting"),
        Fact(subject="Cloud Run", subject_type="tool", predicate="related_to",
             object="Docker", object_type="tool", confidence=0.85,
             reasoning="Cloud Run runs Docker containers"),
        Fact(subject="Engram", subject_type="project", predicate="depends_on",
             object="Cloud Run", object_type="tool", confidence=0.80,
             reasoning="Backend deployment infrastructure"),
    ],
    "meeting_notes": [
        Fact(subject="Saalik", subject_type="person", predicate="decided",
             object="MCP integration", object_type="concept", confidence=0.90,
             reasoning="Decided to add Model Context Protocol support"),
        Fact(subject="Alex", subject_type="person", predicate="asked_about",
             object="temporal awareness", object_type="concept", confidence=0.80,
             reasoning="Asked about how temporal versioning handles conflicts"),
        Fact(subject="MCP integration", subject_type="concept", predicate="part_of",
             object="Engram", object_type="project", confidence=0.85,
             reasoning="MCP server integration for Claude Desktop"),
    ],
}

# ── Request/Response Models ─────────────────────────────────────────────────


class SearchReq(BaseModel):
    query: str
    top_k: int = 10


class IngestReq(BaseModel):
    scenario: str | None = None
    text: str | None = None


class ScoreBreakdown(BaseModel):
    vector: float = 0.0
    graph: float = 0.0
    temporal: float = 0.0


class SearchResult(BaseModel):
    context: str
    facts: list[dict[str, Any]] = Field(default_factory=list)
    scores: ScoreBreakdown
    weights: ScoreBreakdown
    retrieval_ms: float
    source_counts: dict[str, int] = Field(default_factory=dict)


class ComparisonResult(BaseModel):
    engram: SearchResult
    naive: SearchResult


class GraphNode(BaseModel):
    id: str
    name: str
    entity_type: str
    summary: str
    confidence: float


class GraphEdge(BaseModel):
    from_id: str
    to_id: str
    rel_type: str
    summary: str
    confidence: float
    active: bool


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ── Global State ────────────────────────────────────────────────────────────

_graph: KuzuBackend | None = None
_vector: LanceDBBackend | None = None
_metadata: MetadataBackend | None = None
_embedder: Embedder | None = None
_engine: RetrievalEngine | None = None

USER_ID = "saalik"
TENANT_ID = "default"


async def _ingest_facts(facts: list[Fact]) -> dict[str, int]:
    """Ingest a list of facts into the knowledge graph."""
    assert _graph and _embedder

    resolver = EntityResolver(_graph._config if hasattr(_graph, '_config') else EngramConfig(
        local=True, storage_path=str(Path(__file__).parent.parent / "demo_api_data"),
        embedding_model="all-MiniLM-L6-v2", embedding_dim=384,
    ), _graph, _embedder)
    linker = TemporalLinker(_graph)

    resolved = await resolver.resolve(facts, USER_ID, TENANT_ID, f"demo_{generate_id('sess')}")
    new_entities, new_relationships, conflicts = await linker.link(resolved, f"demo_{generate_id('sess')}")

    for entity in new_entities:
        await _graph.create_entity(entity)
        if entity.embedding and _vector:
            await _vector.upsert(
                entity_id=entity.id,
                user_id=entity.user_id,
                tenant_id=entity.tenant_id,
                embedding=entity.embedding,
                summary=entity.summary,
                entity_type=entity.entity_type,
            )

    for rel in new_relationships:
        await _graph.create_relationship(rel)

    return {
        "entities_created": len(new_entities),
        "relationships_created": len(new_relationships),
        "conflicts_detected": conflicts,
    }


# ── Lifespan ────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph, _vector, _metadata, _embedder, _engine

    storage_path = Path(__file__).parent.parent / "demo_api_data"

    config = EngramConfig(
        local=True,
        storage_path=str(storage_path),
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
    )

    print("[demo-api] Initializing backends...")
    _graph = KuzuBackend(config)
    await _graph.initialize()

    _vector = LanceDBBackend(config)
    await _vector.initialize()

    _metadata = MetadataBackend(config)
    await _metadata.initialize()

    _embedder = Embedder(config)

    _engine = RetrievalEngine(
        config=config,
        graph=_graph,
        vector=_vector,
        embedder=_embedder,
    )

    await _metadata.ensure_tenant(TENANT_ID)
    await _metadata.ensure_user(USER_ID, TENANT_ID)

    # Check if data already loaded
    existing = await _graph.list_entities(user_id=USER_ID, tenant_id=TENANT_ID, limit=1)
    if not existing:
        print("[demo-api] Ingesting sample facts...")
        result = await _ingest_facts(SAMPLE_FACTS)
        print(f"[demo-api] Loaded: {result}")
    else:
        print("[demo-api] Demo data already present, skipping ingest.")

    print("[demo-api] Ready!")
    yield

    await _graph.close()
    await _vector.close()
    await _metadata.close()
    _graph = _vector = _metadata = _embedder = _engine = None


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="Engram Demo API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiter
_rate_limit: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 30  # requests per minute


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ("/api/health", "/docs", "/openapi.json"):
        return await call_next(request)

    ip = request.client.host if request.client else "unknown"
    now = time.time()
    _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < 60]

    if len(_rate_limit[ip]) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})

    _rate_limit[ip].append(now)
    return await call_next(request)


# ── Endpoints ───────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {"status": "ok", "entities": len(await _graph.list_entities(
        user_id=USER_ID, tenant_id=TENANT_ID, limit=200
    )) if _graph else 0}


@app.get("/api/graph", response_model=GraphData)
async def get_graph():
    """Return full graph data as JSON for the frontend visualizer."""
    assert _graph

    entities = await _graph.list_entities(user_id=USER_ID, tenant_id=TENANT_ID, limit=200)

    nodes = []
    for e in entities:
        nodes.append(GraphNode(
            id=e.id,
            name=e.name,
            entity_type=e.entity_type,
            summary=e.summary,
            confidence=e.confidence,
        ))

    edges = []
    seen = set()
    for e in entities:
        rels = await _graph.get_active_relationships(e.id)
        for r in rels:
            if r.id not in seen:
                edges.append(GraphEdge(
                    from_id=r.from_entity_id,
                    to_id=r.to_entity_id,
                    rel_type=r.rel_type.value if hasattr(r.rel_type, "value") else str(r.rel_type),
                    summary=r.summary or r.reasoning,
                    confidence=r.confidence,
                    active=r.is_active,
                ))
                seen.add(r.id)

    return GraphData(nodes=nodes, edges=edges)


@app.post("/api/search", response_model=ComparisonResult)
async def search(req: SearchReq):
    """Hybrid search with side-by-side naive RAG comparison."""
    assert _engine and _graph and _vector and _embedder

    start = time.monotonic()

    # ── Engram hybrid search ──
    weights = classify_query(req.query)

    vector_results, graph_results, temporal_results = await asyncio.gather(
        vector_search(
            query=req.query, user_id=USER_ID, tenant_id=TENANT_ID,
            vector_store=_vector, embedder=_embedder, top_k=50,
        ),
        graph_search(
            query=req.query, user_id=USER_ID, tenant_id=TENANT_ID,
            graph=_graph, max_hops=3,
        ),
        temporal_search(
            query=req.query, user_id=USER_ID, tenant_id=TENANT_ID,
            graph=_graph, config=_engine.config, session_id=None,
        ),
    )

    fused = fuse_candidates(vector_results, graph_results, temporal_results, weights)
    context = await assemble_context(
        ranked_nodes=fused[:req.top_k * 3],
        graph=_graph,
        token_budget=4000,
    )

    elapsed = (time.monotonic() - start) * 1000

    # Compute average per-source scores for visualization
    avg_scores = _avg_source_scores(vector_results, graph_results, temporal_results)

    engram_result = SearchResult(
        context=context.text,
        facts=[f.model_dump() for f in context.facts],
        scores=ScoreBreakdown(**avg_scores),
        weights=ScoreBreakdown(
            vector=weights.vector, graph=weights.graph, temporal=weights.temporal,
        ),
        retrieval_ms=round(elapsed, 1),
        source_counts={
            "vector": len(vector_results),
            "graph": len(graph_results),
            "temporal": len(temporal_results),
        },
    )

    # ── Naive vector-only search ──
    naive_start = time.monotonic()
    from engram.types import RetrievalWeights
    naive_weights = RetrievalWeights(vector=1.0, graph=0.0, temporal=0.0)
    naive_fused = fuse_candidates(vector_results, [], [], naive_weights)
    naive_context = await assemble_context(
        ranked_nodes=naive_fused[:req.top_k * 3],
        graph=_graph,
        token_budget=4000,
    )
    naive_elapsed = (time.monotonic() - naive_start) * 1000

    naive_result = SearchResult(
        context=naive_context.text,
        facts=[f.model_dump() for f in naive_context.facts],
        scores=ScoreBreakdown(vector=1.0, graph=0.0, temporal=0.0),
        weights=ScoreBreakdown(vector=1.0, graph=0.0, temporal=0.0),
        retrieval_ms=round(naive_elapsed, 1),
        source_counts={"vector": len(vector_results), "graph": 0, "temporal": 0},
    )

    return ComparisonResult(engram=engram_result, naive=naive_result)


@app.post("/api/ingest")
async def ingest(req: IngestReq):
    """Ingest a pre-loaded scenario or custom text."""
    if req.scenario and req.scenario in SCENARIO_FACTS:
        result = await _ingest_facts(SCENARIO_FACTS[req.scenario])
        return {"status": "ok", "scenario": req.scenario, **result}

    return {
        "status": "error",
        "message": f"Unknown scenario. Available: {list(SCENARIO_FACTS.keys())}",
    }


@app.get("/api/scenarios")
async def list_scenarios():
    """List available ingest scenarios."""
    return {
        name: {
            "fact_count": len(facts),
            "description": facts[0].reasoning if facts else "",
        }
        for name, facts in SCENARIO_FACTS.items()
    }


# ── Helpers ─────────────────────────────────────────────────────────────────


def _avg_source_scores(
    vector_results: list[ScoredNode],
    graph_results: list[ScoredNode],
    temporal_results: list[ScoredNode],
) -> dict[str, float]:
    """Compute normalized average scores per source for visualization."""
    def avg(nodes: list[ScoredNode]) -> float:
        if not nodes:
            return 0.0
        return sum(n.score for n in nodes) / len(nodes)

    v, g, t = avg(vector_results), avg(graph_results), avg(temporal_results)
    total = v + g + t
    if total == 0:
        return {"vector": 0.33, "graph": 0.33, "temporal": 0.33}
    return {"vector": v / total, "graph": g / total, "temporal": t / total}
