"""Hybrid retrieval engine — orchestrates vector, graph, temporal search + fusion."""

from __future__ import annotations

import asyncio
import time

from engram.config import EngramConfig
from engram.ingestion.embedder import Embedder
from engram.retrieval.classifier import classify_query
from engram.retrieval.context_assembler import assemble_context
from engram.retrieval.fusion import fuse_candidates, fuse_global_candidates
from engram.retrieval.global_search import global_search
from engram.retrieval.graph_search import graph_search
from engram.retrieval.temporal_search import temporal_search
from engram.retrieval.vector_search import vector_search
from engram.storage.kuzu_backend import KuzuBackend
from engram.storage.lancedb_backend import LanceDBBackend
from engram.types import MemoryContext, QueryType


class RetrievalEngine:
    def __init__(
        self,
        config: EngramConfig,
        graph: KuzuBackend,
        vector: LanceDBBackend,
        embedder: Embedder,
    ) -> None:
        self.config = config
        self.graph = graph
        self.vector = vector
        self.embedder = embedder
        self.reranker = None
        if config.reranker_model:
            from engram.retrieval.reranker import Reranker

            self.reranker = Reranker(config)

    async def search(
        self,
        query: str,
        user_id: str,
        tenant_id: str = "default",
        session_id: str | None = None,
        top_k: int = 10,
        token_budget: int = 4000,
        mode: str = "hybrid",
    ) -> MemoryContext:
        """Full retrieval pipeline — hybrid or global mode."""
        start = time.monotonic()

        # Step 1: Classify query
        weights, query_type = classify_query(query)

        # Override query type if explicit mode requested
        if mode == "global":
            query_type = QueryType.GLOBAL

        # Step 2: Retrieval fanout (branched by query type)
        if query_type == QueryType.GLOBAL:
            fused, source_counts = await self._global_retrieval(
                query, user_id, tenant_id
            )
        else:
            fused, source_counts = await self._hybrid_retrieval(
                query, user_id, tenant_id, session_id, weights
            )

        # Step 3: Optional reranker
        if self.reranker is not None:
            fused = await self.reranker.rerank(
                query=query,
                candidates=fused,
                graph=self.graph,
                top_k=top_k * 3,
            )

        # Step 4: Context assembly (token-budget packing)
        context = await assemble_context(
            ranked_nodes=fused[:top_k * 3],
            graph=self.graph,
            token_budget=token_budget,
        )

        # Add retrieval metadata
        elapsed_ms = (time.monotonic() - start) * 1000
        context.retrieval_metadata.update({
            "retrieval_ms": round(elapsed_ms, 1),
            "query_type": query_type.value,
            "mode": mode,
            "weights": {
                "vector": weights.vector,
                "graph": weights.graph,
                "temporal": weights.temporal,
            },
            "sources": source_counts,
            "reranker": self.config.reranker_model or "disabled",
        })

        return context

    async def _hybrid_retrieval(
        self,
        query: str,
        user_id: str,
        tenant_id: str,
        session_id: str | None,
        weights,
    ) -> tuple[list[tuple[str, float]], dict[str, int]]:
        vector_results, graph_results, temporal_results = await asyncio.gather(
            vector_search(
                query=query,
                user_id=user_id,
                tenant_id=tenant_id,
                vector_store=self.vector,
                embedder=self.embedder,
                top_k=50,
            ),
            graph_search(
                query=query,
                user_id=user_id,
                tenant_id=tenant_id,
                graph=self.graph,
                max_hops=self.config.max_hops,
            ),
            temporal_search(
                query=query,
                user_id=user_id,
                tenant_id=tenant_id,
                graph=self.graph,
                config=self.config,
                session_id=session_id,
            ),
        )

        fused = fuse_candidates(vector_results, graph_results, temporal_results, weights)
        source_counts = {
            "vector": len(vector_results),
            "graph": len(graph_results),
            "temporal": len(temporal_results),
        }
        return fused, source_counts

    async def _global_retrieval(
        self,
        query: str,
        user_id: str,
        tenant_id: str,
    ) -> tuple[list[tuple[str, float]], dict[str, int]]:
        global_results, vector_results = await asyncio.gather(
            global_search(
                user_id=user_id,
                tenant_id=tenant_id,
                graph=self.graph,
                top_k=50,
            ),
            vector_search(
                query=query,
                user_id=user_id,
                tenant_id=tenant_id,
                vector_store=self.vector,
                embedder=self.embedder,
                top_k=50,
            ),
        )

        fused = fuse_global_candidates(global_results, vector_results)
        source_counts = {
            "global": len(global_results),
            "vector": len(vector_results),
        }
        return fused, source_counts
