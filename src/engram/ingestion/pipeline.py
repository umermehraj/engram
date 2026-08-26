"""Ingestion pipeline orchestrator — preprocess → extract → resolve → link → write."""

from __future__ import annotations

import logging
from typing import Any

from engram.config import EngramConfig
from engram.exceptions import ExtractionError
from engram.ingestion.embedder import Embedder
from engram.ingestion.extractor import Extractor
from engram.ingestion.preprocessor import preprocess_messages, preprocess_document
from engram.ingestion.resolver import EntityResolver
from engram.ingestion.temporal_linker import TemporalLinker
from engram.storage.kuzu_backend import KuzuBackend
from engram.storage.lancedb_backend import LanceDBBackend
from engram.storage.metadata_backend import MetadataBackend
from engram.types import AddMemoryResponse, Fact
from engram.utils import generate_id

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        config: EngramConfig,
        graph: KuzuBackend,
        vector: LanceDBBackend,
        metadata: MetadataBackend,
        embedder: Embedder,
    ) -> None:
        self.config = config
        self.graph = graph
        self.vector = vector
        self.metadata = metadata
        self.embedder = embedder
        self.extractor = Extractor(config)
        self.resolver = EntityResolver(config, graph, embedder)
        self.temporal_linker = TemporalLinker(graph)

    async def run(
        self,
        *,
        messages: list[dict[str, str]] | None = None,
        text: str | None = None,
        user_id: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str = "default",
    ) -> AddMemoryResponse:
        """Run the full ingestion pipeline."""
        # Ensure tenant/user exist in metadata store
        await self.metadata.ensure_tenant(tenant_id)
        await self.metadata.ensure_user(user_id, tenant_id)

        # Step 1: Preprocess
        if messages:
            input_text = preprocess_messages(messages)
        elif text:
            chunks = preprocess_document(text)
            input_text = "\n\n".join(chunks)
        else:
            return AddMemoryResponse()

        if not input_text.strip():
            return AddMemoryResponse()

        # Step 2: Extract facts via LLM
        try:
            facts = await self.extractor.extract_facts(input_text, session_id)
        except ExtractionError:
            logger.warning("LLM extraction failed, skipping ingestion")
            return AddMemoryResponse()

        if not facts:
            return AddMemoryResponse()

        # Step 3: Resolve entities (dedup / merge)
        resolved = await self.resolver.resolve(facts, user_id, tenant_id, session_id)

        # Step 4: Temporal linking (conflict detection, versioning)
        new_entities, new_relationships, conflicts = await self.temporal_linker.link(
            resolved, session_id
        )

        # Step 5: Dual-write to all stores
        entities_created = 0
        relationships_created = 0

        for entity in new_entities:
            await self.graph.create_entity(entity)
            if entity.embedding:
                await self.vector.upsert(
                    entity_id=entity.id,
                    user_id=entity.user_id,
                    tenant_id=entity.tenant_id,
                    embedding=entity.embedding,
                    summary=entity.summary,
                    entity_type=entity.entity_type,
                )
            entities_created += 1

        for rel in new_relationships:
            await self.graph.create_relationship(rel)
            relationships_created += 1

        # Log to metadata store
        await self.metadata.log_ingestion(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id or "",
            entities_created=entities_created,
            relationships_created=relationships_created,
        )

        return AddMemoryResponse(
            entities_created=entities_created,
            entities_merged=len(facts) * 2 - entities_created,  # approx merged count
            relationships_created=relationships_created,
            conflicts_detected=conflicts,
        )

    async def add_fact(
        self,
        *,
        subject: str,
        predicate: str,
        object: str,
        user_id: str,
        tenant_id: str = "default",
        confidence: float = 0.95,
        session_id: str | None = None,
    ) -> AddMemoryResponse:
        """Direct fact ingestion (no LLM extraction needed)."""
        fact = Fact(
            subject=subject,
            subject_type="concept",
            predicate=predicate,
            object=object,
            object_type="concept",
            confidence=confidence,
            source_session_id=session_id,
        )

        await self.metadata.ensure_tenant(tenant_id)
        await self.metadata.ensure_user(user_id, tenant_id)

        resolved = await self.resolver.resolve([fact], user_id, tenant_id, session_id)
        new_entities, new_relationships, conflicts = await self.temporal_linker.link(
            resolved, session_id
        )

        entities_created = 0
        for entity in new_entities:
            await self.graph.create_entity(entity)
            if entity.embedding:
                await self.vector.upsert(
                    entity_id=entity.id,
                    user_id=entity.user_id,
                    tenant_id=entity.tenant_id,
                    embedding=entity.embedding,
                    summary=entity.summary,
                    entity_type=entity.entity_type,
                )
            entities_created += 1

        for rel in new_relationships:
            await self.graph.create_relationship(rel)

        return AddMemoryResponse(
            entities_created=entities_created,
            relationships_created=len(new_relationships),
            conflicts_detected=conflicts,
        )
