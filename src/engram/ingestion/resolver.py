"""Entity resolution — deduplicate via fuzzy name match + embedding similarity."""

from __future__ import annotations

from engram.config import EngramConfig
from engram.ingestion.embedder import Embedder
from engram.storage.kuzu_backend import KuzuBackend
from engram.types import Entity, Fact
from engram.utils import cosine_similarity, levenshtein_ratio, generate_id


class EntityResolver:
    def __init__(
        self,
        config: EngramConfig,
        graph: KuzuBackend,
        embedder: Embedder,
    ) -> None:
        self.config = config
        self.graph = graph
        self.embedder = embedder

    async def resolve(
        self,
        facts: list[Fact],
        user_id: str,
        tenant_id: str,
        session_id: str | None,
    ) -> list[tuple[Fact, Entity, Entity]]:
        """
        For each fact, resolve subject and object to existing or new entities.
        Returns list of (fact, subject_entity, object_entity).
        """
        # Cache: name -> Entity (to avoid re-resolving within same batch)
        cache: dict[str, Entity] = {}
        results = []

        for fact in facts:
            subj = await self._resolve_entity(
                name=fact.subject,
                entity_type=fact.subject_type,
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                cache=cache,
            )
            obj = await self._resolve_entity(
                name=fact.object,
                entity_type=fact.object_type,
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                cache=cache,
            )
            results.append((fact, subj, obj))

        return results

    async def _resolve_entity(
        self,
        name: str,
        entity_type: str,
        user_id: str,
        tenant_id: str,
        session_id: str | None,
        cache: dict[str, Entity],
    ) -> Entity:
        """Find existing entity or create a new one."""
        cache_key = f"{name.lower().strip()}:{entity_type}"
        if cache_key in cache:
            return cache[cache_key]

        # Look for existing entities of the same type
        candidates = await self.graph.find_similar_entities(
            name=name, entity_type=entity_type, user_id=user_id, tenant_id=tenant_id
        )

        # Check fuzzy name match
        for candidate in candidates:
            ratio = levenshtein_ratio(name, candidate.name)
            if ratio >= self.config.dedup_fuzzy_threshold:
                # Also check embedding similarity if both have embeddings
                if candidate.embedding:
                    query_emb = await self.embedder.embed(name)
                    sim = cosine_similarity(query_emb, candidate.embedding)
                    if sim >= self.config.dedup_similarity_threshold:
                        cache[cache_key] = candidate
                        return candidate
                else:
                    # Fuzzy match alone is enough
                    cache[cache_key] = candidate
                    return candidate

        # No match — create new entity
        embedding = await self.embedder.embed(f"{name} ({entity_type})")
        entity = Entity(
            id=generate_id("ent"),
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            entity_type=entity_type,
            summary=f"{name} ({entity_type})",
            embedding=embedding,
            source_session_id=session_id,
        )
        cache[cache_key] = entity
        return entity
