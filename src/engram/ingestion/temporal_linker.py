"""Temporal linking — conflict detection and edge versioning."""

from __future__ import annotations

import logging
from datetime import datetime

from engram.storage.kuzu_backend import KuzuBackend
from engram.types import Entity, Fact, Relationship, RelType
from engram.utils import generate_id

logger = logging.getLogger(__name__)


class TemporalLinker:
    def __init__(self, graph: KuzuBackend) -> None:
        self.graph = graph

    async def link(
        self,
        resolved_facts: list[tuple[Fact, Entity, Entity]],
        session_id: str | None,
    ) -> tuple[list[Entity], list[Relationship], int]:
        """
        Process resolved facts: create/update entities and relationships.
        Returns (new_entities, new_relationships, conflicts_detected).
        """
        new_entities: list[Entity] = []
        new_relationships: list[Relationship] = []
        conflicts = 0
        created_entity_ids: set[str] = set()

        for fact, subj_entity, obj_entity in resolved_facts:
            # Create entities if they don't exist in graph yet
            for entity in (subj_entity, obj_entity):
                if entity.id not in created_entity_ids:
                    existing = await self.graph.get_entity(entity.id)
                    if existing is None:
                        new_entities.append(entity)
                    created_entity_ids.add(entity.id)

            # Resolve relationship type
            try:
                rel_type = RelType(fact.predicate)
            except ValueError:
                rel_type = RelType.RELATED_TO

            # Check for existing active relationship of the same type
            existing_rel = await self.graph.find_active_relationship(
                from_id=subj_entity.id,
                to_id=obj_entity.id,
                rel_type=rel_type.value,
            )

            now = datetime.utcnow()

            if existing_rel and fact.is_update:
                # Invalidate old relationship
                await self.graph.invalidate_relationship(existing_rel.id, now)
                conflicts += 1
                logger.info(
                    f"Invalidated relationship {existing_rel.id} "
                    f"({subj_entity.name} -> {obj_entity.name})"
                )

            # Create new relationship (unless exact duplicate exists and not an update)
            if not existing_rel or fact.is_update:
                rel = Relationship(
                    id=generate_id("rel"),
                    from_entity_id=subj_entity.id,
                    to_entity_id=obj_entity.id,
                    rel_type=rel_type,
                    summary=f"{subj_entity.name} {fact.predicate} {obj_entity.name}",
                    confidence=fact.confidence,
                    valid_from=now,
                    source_session_id=session_id,
                    reasoning=fact.reasoning,
                )
                new_relationships.append(rel)

        return new_entities, new_relationships, conflicts
