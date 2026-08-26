#!/usr/bin/env python3
"""
Engram Interactive Demo
=======================

Demonstrates the full pipeline: ingest conversations → build knowledge graph →
visualize as interactive nodes/edges → search with hybrid retrieval.

Usage:
    python demo.py

This will:
1. Create a local Engram instance (no API keys needed for the graph/viz parts)
2. Ingest sample conversations with pre-extracted facts (no LLM needed)
3. Build the knowledge graph with entities and relationships
4. Render an interactive HTML visualization
5. Run sample searches and show retrieval results
6. Open the graph in your browser
"""

import asyncio
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from engram.config import EngramConfig
from engram.storage.kuzu_backend import KuzuBackend
from engram.storage.lancedb_backend import LanceDBBackend
from engram.storage.metadata_backend import MetadataBackend
from engram.ingestion.embedder import Embedder
from engram.ingestion.temporal_linker import TemporalLinker
from engram.ingestion.resolver import EntityResolver
from engram.retrieval.engine import RetrievalEngine
from engram.types import Entity, Relationship, RelType, Fact
from engram.utils import generate_id
from engram.viz.graph_view import build_graph_html, visualize_user_graph


# ── Sample Data ──────────────────────────────────────────────────────────────
# Pre-extracted facts simulating what the LLM extractor would produce
# from real conversations. No API key needed for this demo.

SAMPLE_FACTS = [
    # ── Data Sources (the actual artifacts ingested) ──────────────────────
    # Each conversation/document/file becomes a node in the graph

    # Conversation: tech stack discussion → extracted facts connect to it
    Fact(subject="Chat: Tech Stack Discussion", subject_type="conversation",
         predicate="mentioned", object="FastAPI", object_type="tool", confidence=0.95,
         reasoning="Conversation where tech stack was decided"),
    Fact(subject="Chat: Tech Stack Discussion", subject_type="conversation",
         predicate="mentioned", object="Django", object_type="tool", confidence=0.80,
         reasoning="Django was discussed as alternative"),
    Fact(subject="Saalik", subject_type="person", predicate="decided",
         object="FastAPI", object_type="tool", confidence=0.95,
         reasoning="Explicitly chose FastAPI for the backend"),
    Fact(subject="Saalik", subject_type="person", predicate="replaced",
         object="Django", object_type="tool", confidence=0.95,
         reasoning="Replaced Django with FastAPI"),

    # Document: MVP spec → extracted facts
    Fact(subject="Doc: MVP Spec v1", subject_type="document",
         predicate="mentioned", object="Engram", object_type="project", confidence=0.99,
         reasoning="The MVP spec document for the project"),
    Fact(subject="Doc: MVP Spec v1", subject_type="document",
         predicate="mentioned", object="Kuzu", object_type="tool", confidence=0.95,
         reasoning="Kuzu specified as graph database"),
    Fact(subject="Doc: MVP Spec v1", subject_type="document",
         predicate="mentioned", object="LanceDB", object_type="tool", confidence=0.95,
         reasoning="LanceDB specified as vector store"),
    Fact(subject="Doc: MVP Spec v1", subject_type="document",
         predicate="mentioned", object="hybrid retrieval", object_type="concept",
         confidence=0.90, reasoning="Core concept in the spec"),

    # Image: architecture diagram → extracted facts
    Fact(subject="Img: Architecture Diagram", subject_type="image",
         predicate="related_to", object="Engram", object_type="project", confidence=0.95,
         reasoning="Visual architecture of the system"),
    Fact(subject="Img: Architecture Diagram", subject_type="image",
         predicate="mentioned", object="API Gateway", object_type="concept",
         confidence=0.85, reasoning="Shows API gateway in architecture"),

    # Code file → extracted facts
    Fact(subject="Code: retrieval/engine.py", subject_type="code",
         predicate="part_of", object="Engram", object_type="project", confidence=0.99,
         reasoning="Core retrieval engine implementation"),
    Fact(subject="Code: retrieval/engine.py", subject_type="code",
         predicate="depends_on", object="FastAPI", object_type="tool", confidence=0.85,
         reasoning="Uses FastAPI for API endpoints"),

    # Audio: meeting recording → extracted facts
    Fact(subject="Audio: Team Standup Mar 20", subject_type="audio",
         predicate="mentioned", object="Saalik", object_type="person", confidence=0.90,
         reasoning="Saalik spoke about progress"),
    Fact(subject="Audio: Team Standup Mar 20", subject_type="audio",
         predicate="mentioned", object="AI agents", object_type="concept",
         confidence=0.85, reasoning="Discussion about AI agent integration"),

    # Webpage: competitor research
    Fact(subject="Web: Mem0 Docs", subject_type="webpage",
         predicate="related_to", object="Mem0", object_type="tool", confidence=0.90,
         reasoning="Competitor documentation page"),
    Fact(subject="Web: Zep GitHub", subject_type="webpage",
         predicate="related_to", object="Zep", object_type="tool", confidence=0.90,
         reasoning="Competitor GitHub repository"),

    # ── Entity-to-entity relationships ────────────────────────────────────
    Fact(subject="Engram", subject_type="project", predicate="depends_on",
         object="Kuzu", object_type="tool", confidence=0.95,
         reasoning="Uses Kuzu as embedded graph database"),
    Fact(subject="Engram", subject_type="project", predicate="depends_on",
         object="LanceDB", object_type="tool", confidence=0.95,
         reasoning="Uses LanceDB for vector search"),
    Fact(subject="FastAPI", subject_type="tool", predicate="depends_on",
         object="Uvicorn", object_type="tool", confidence=0.90,
         reasoning="FastAPI runs on Uvicorn ASGI server"),
    Fact(subject="Saalik", subject_type="person", predicate="works_on",
         object="Engram", object_type="project", confidence=0.99,
         reasoning="Building the Engram memory layer"),
    Fact(subject="Saalik", subject_type="person", predicate="prefers",
         object="Python", object_type="tool", confidence=0.90,
         reasoning="Primary language choice"),
    Fact(subject="Saalik", subject_type="person", predicate="believes",
         object="hybrid retrieval", object_type="concept", confidence=0.88,
         reasoning="Believes hybrid retrieval outperforms single-method"),
    Fact(subject="Saalik", subject_type="person", predicate="works_on",
         object="AI agents", object_type="concept", confidence=0.85,
         reasoning="Working in the AI agent space"),
    Fact(subject="Engram", subject_type="project", predicate="related_to",
         object="Mem0", object_type="tool", confidence=0.70,
         reasoning="Competitor in the memory layer space"),
    Fact(subject="Engram", subject_type="project", predicate="related_to",
         object="Zep", object_type="tool", confidence=0.70,
         reasoning="Competitor with different approach"),
    Fact(subject="Kuzu", subject_type="tool", predicate="part_of",
         object="Engram", object_type="project", confidence=0.95,
         reasoning="Core storage component"),
    Fact(subject="LanceDB", subject_type="tool", predicate="part_of",
         object="Engram", object_type="project", confidence=0.95,
         reasoning="Core storage component"),
]


async def run_demo():
    print("\n" + "=" * 60)
    print("  🧠 Engram Interactive Demo")
    print("=" * 60)

    # Setup
    storage_path = Path("./demo_data")
    config = EngramConfig(
        local=True,
        storage_path=str(storage_path),
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
    )

    print("\n[1/5] Initializing storage backends...")
    graph = KuzuBackend(config)
    await graph.initialize()

    vector = LanceDBBackend(config)
    await vector.initialize()

    metadata = MetadataBackend(config)
    await metadata.initialize()

    embedder = Embedder(config)

    print("  ✓ Kuzu graph DB ready")
    print("  ✓ LanceDB vector store ready")
    print("  ✓ SQLite metadata ready")
    print("  ✓ Sentence-transformers embedder ready")

    # Resolve and ingest facts
    print("\n[2/5] Ingesting sample facts into knowledge graph...")
    resolver = EntityResolver(config, graph, embedder)
    linker = TemporalLinker(graph)

    user_id = "saalik"
    tenant_id = "default"

    await metadata.ensure_tenant(tenant_id)
    await metadata.ensure_user(user_id, tenant_id)

    resolved = await resolver.resolve(SAMPLE_FACTS, user_id, tenant_id, "demo_session_1")
    new_entities, new_relationships, conflicts = await linker.link(resolved, "demo_session_1")

    # Write entities to graph and vector store
    for entity in new_entities:
        await graph.create_entity(entity)
        if entity.embedding:
            await vector.upsert(
                entity_id=entity.id,
                user_id=entity.user_id,
                tenant_id=entity.tenant_id,
                embedding=entity.embedding,
                summary=entity.summary,
                entity_type=entity.entity_type,
            )

    for rel in new_relationships:
        await graph.create_relationship(rel)

    print(f"  ✓ Created {len(new_entities)} entities")
    print(f"  ✓ Created {len(new_relationships)} relationships")
    print(f"  ✓ Detected {conflicts} temporal conflicts")

    # Visualize
    print("\n[3/5] Generating interactive knowledge graph visualization...")
    output_path = str(storage_path / "engram_graph.html")
    await visualize_user_graph(
        graph_backend=graph,
        user_id=user_id,
        tenant_id=tenant_id,
        output_path=output_path,
    )
    print(f"  ✓ Graph saved to: {output_path}")

    # Run sample searches
    print("\n[4/5] Running hybrid retrieval searches...")
    engine = RetrievalEngine(
        config=config,
        graph=graph,
        vector=vector,
        embedder=embedder,
    )

    queries = [
        "What backend framework are we using?",
        "What does Engram depend on?",
        "What are Saalik's preferences?",
        "When did we switch from Django?",
    ]

    for query in queries:
        print(f"\n  Query: \"{query}\"")
        ctx = await engine.search(
            query=query,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        print(f"  Retrieval: {ctx.retrieval_metadata.get('retrieval_ms', '?')}ms "
              f"| {ctx.retrieval_metadata.get('blocks_returned', 0)} blocks "
              f"| {ctx.total_tokens} tokens")
        if ctx.text:
            # Show first 200 chars of context
            preview = ctx.text[:200].replace('\n', ' ')
            print(f"  Context: {preview}...")
        else:
            print("  Context: (empty — entities may not match query)")

    # Open in browser
    print("\n[5/5] Opening graph visualization in browser...")
    abs_path = str(Path(output_path).resolve())
    webbrowser.open(f"file://{abs_path}")

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print(f"  Graph visualization: {abs_path}")
    print("  Interact: zoom, pan, hover nodes, drag to rearrange")
    print("=" * 60 + "\n")

    # Cleanup
    await graph.close()
    await vector.close()
    await metadata.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
