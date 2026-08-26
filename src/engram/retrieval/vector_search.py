"""Vector search — ANN over entity summaries in LanceDB."""

from __future__ import annotations

from engram.ingestion.embedder import Embedder
from engram.storage.lancedb_backend import LanceDBBackend
from engram.types import ScoredNode


async def vector_search(
    query: str,
    user_id: str,
    tenant_id: str,
    vector_store: LanceDBBackend,
    embedder: Embedder,
    top_k: int = 50,
) -> list[ScoredNode]:
    """Embed query and search LanceDB for similar entity summaries."""
    query_embedding = await embedder.embed(query)

    results = await vector_store.search(
        query_embedding=query_embedding,
        user_id=user_id,
        tenant_id=tenant_id,
        top_k=top_k,
    )

    return [
        ScoredNode(
            node_id=entity_id,
            # LanceDB returns distance; convert to similarity score (lower distance = higher score)
            score=1.0 / (1.0 + distance),
            source="vector",
        )
        for entity_id, distance in results
    ]
