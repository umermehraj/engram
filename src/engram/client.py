"""Main MemoryClient — public API for Engram."""

from __future__ import annotations

from typing import Any

from engram.config import EngramConfig
from engram.types import (
    AddMemoryResponse,
    MemoryContext,
    MemoryVersion,
    Entity,
)


class MemoryClient:
    """
    Primary interface for Engram.

    Usage (local/embedded mode):
        memory = MemoryClient(local=True)
        await memory.add(messages=[...], user_id="user_123")
        ctx = await memory.search("What framework?", user_id="user_123")

    Usage (cloud mode):
        memory = MemoryClient(api_key="sk-...")
        ...
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        local: bool = False,
        storage_path: str | None = None,
        config: EngramConfig | None = None,
    ) -> None:
        overrides: dict[str, Any] = {}
        if api_key is not None:
            overrides["api_key"] = api_key
        if storage_path is not None:
            overrides["storage_path"] = storage_path
        if local:
            overrides["local"] = True

        self.config = config or EngramConfig.from_env(**overrides)
        self._initialized = False

        # Lazily initialized backends
        self._graph = None
        self._vector = None
        self._metadata = None
        self._embedder = None
        self._ingestion_pipeline = None
        self._retrieval_engine = None

    async def _ensure_initialized(self) -> None:
        """Lazy-init storage backends on first use."""
        if self._initialized:
            return

        from engram.storage.kuzu_backend import KuzuBackend
        from engram.storage.lancedb_backend import LanceDBBackend
        from engram.storage.metadata_backend import MetadataBackend
        from engram.ingestion.embedder import Embedder
        from engram.ingestion.pipeline import IngestionPipeline
        from engram.retrieval.engine import RetrievalEngine

        self._graph = KuzuBackend(self.config)
        await self._graph.initialize()

        self._vector = LanceDBBackend(self.config)
        await self._vector.initialize()

        self._metadata = MetadataBackend(self.config)
        await self._metadata.initialize()

        self._embedder = Embedder(self.config)

        self._ingestion_pipeline = IngestionPipeline(
            config=self.config,
            graph=self._graph,
            vector=self._vector,
            metadata=self._metadata,
            embedder=self._embedder,
        )

        self._retrieval_engine = RetrievalEngine(
            config=self.config,
            graph=self._graph,
            vector=self._vector,
            embedder=self._embedder,
        )

        self._initialized = True

    async def add(
        self,
        *,
        messages: list[dict[str, str]] | None = None,
        text: str | None = None,
        user_id: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str = "default",
    ) -> AddMemoryResponse:
        """Ingest messages, documents, or raw text into memory."""
        await self._ensure_initialized()
        assert self._ingestion_pipeline is not None
        return await self._ingestion_pipeline.run(
            messages=messages,
            text=text,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            tenant_id=tenant_id,
        )

    async def search(
        self,
        query: str,
        *,
        user_id: str,
        session_id: str | None = None,
        top_k: int = 10,
        token_budget: int = 4000,
        mode: str = "hybrid",
        filters: dict[str, Any] | None = None,
        tenant_id: str = "default",
    ) -> MemoryContext:
        """Search memory using hybrid or global retrieval."""
        await self._ensure_initialized()
        assert self._retrieval_engine is not None
        return await self._retrieval_engine.search(
            query=query,
            user_id=user_id,
            session_id=session_id,
            top_k=top_k,
            token_budget=token_budget,
            mode=mode,
            tenant_id=tenant_id,
        )

    async def get_all(
        self,
        *,
        user_id: str,
        tenant_id: str = "default",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        """List all entities for a user."""
        await self._ensure_initialized()
        assert self._graph is not None
        return await self._graph.list_entities(
            user_id=user_id, tenant_id=tenant_id, limit=limit, offset=offset
        )

    async def history(
        self,
        *,
        user_id: str,
        entity_name: str | None = None,
        tenant_id: str = "default",
    ) -> list[MemoryVersion]:
        """Get temporal version chain for an entity."""
        await self._ensure_initialized()
        assert self._graph is not None
        return await self._graph.get_history(
            user_id=user_id, entity_name=entity_name, tenant_id=tenant_id
        )

    async def delete(self, *, memory_id: str) -> bool:
        """Soft-delete a specific memory (entity + relationships)."""
        await self._ensure_initialized()
        assert self._graph is not None and self._vector is not None
        await self._graph.delete_entity(memory_id)
        await self._vector.delete_by_entity_id(memory_id)
        return True

    async def delete_user(self, *, user_id: str, tenant_id: str = "default") -> int:
        """GDPR: delete ALL data for a user across all stores."""
        await self._ensure_initialized()
        assert (
            self._graph is not None
            and self._vector is not None
            and self._metadata is not None
        )
        count = 0
        count += await self._graph.delete_user_data(user_id, tenant_id)
        count += await self._vector.delete_user_data(user_id, tenant_id)
        count += await self._metadata.delete_user_data(user_id, tenant_id)
        return count

    async def close(self) -> None:
        """Clean up resources."""
        if self._graph:
            await self._graph.close()
        if self._vector:
            await self._vector.close()
        if self._metadata:
            await self._metadata.close()
        self._initialized = False
