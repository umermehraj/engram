"""Kuzu embedded graph database backend."""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import partial
from typing import Any

import kuzu

from engram.config import EngramConfig
from engram.exceptions import StorageError
from engram.storage.base import GraphBackend
from engram.types import Entity, Relationship, MemoryVersion, RelType


class KuzuBackend(GraphBackend):
    def __init__(self, config: EngramConfig) -> None:
        self.config = config
        self._db: kuzu.Database | None = None
        self._conn: kuzu.Connection | None = None

    async def initialize(self) -> None:
        self.config.kuzu_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = kuzu.Database(str(self.config.kuzu_path))
        self._conn = kuzu.Connection(self._db)
        await self._create_schema()

    async def _create_schema(self) -> None:
        conn = self._conn
        assert conn is not None

        def _run():
            # Create Entity node table if not exists
            try:
                conn.execute("""
                    CREATE NODE TABLE IF NOT EXISTS Entity (
                        id STRING PRIMARY KEY,
                        tenant_id STRING,
                        user_id STRING,
                        name STRING,
                        entity_type STRING,
                        summary STRING,
                        confidence DOUBLE,
                        created_at TIMESTAMP,
                        last_referenced_at TIMESTAMP,
                        source_session_id STRING,
                        metadata STRING
                    )
                """)
            except RuntimeError:
                pass  # Table may already exist in older Kuzu versions

            # Create Relationship edge table
            try:
                conn.execute("""
                    CREATE REL TABLE IF NOT EXISTS Rel (
                        FROM Entity TO Entity,
                        id STRING,
                        rel_type STRING,
                        summary STRING,
                        confidence DOUBLE,
                        valid_from TIMESTAMP,
                        invalid_from TIMESTAMP,
                        source_session_id STRING,
                        source_message_idx INT64,
                        reasoning STRING,
                        metadata STRING
                    )
                """)
            except RuntimeError:
                pass

        await asyncio.get_event_loop().run_in_executor(None, _run)

    def _run_sync(self, fn, *args, **kwargs):
        """Run a sync Kuzu operation in the thread pool."""
        return asyncio.get_event_loop().run_in_executor(None, partial(fn, *args, **kwargs))

    async def create_entity(self, entity: Entity) -> None:
        conn = self._conn
        assert conn is not None

        def _insert():
            conn.execute(
                """
                CREATE (e:Entity {
                    id: $id, tenant_id: $tenant_id, user_id: $user_id,
                    name: $name, entity_type: $entity_type, summary: $summary,
                    confidence: $confidence, created_at: $created_at,
                    last_referenced_at: $last_referenced_at,
                    source_session_id: $source_session_id,
                    metadata: $metadata
                })
                """,
                {
                    "id": entity.id,
                    "tenant_id": entity.tenant_id,
                    "user_id": entity.user_id,
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "summary": entity.summary,
                    "confidence": entity.confidence,
                    "created_at": entity.created_at,
                    "last_referenced_at": entity.last_referenced_at,
                    "source_session_id": entity.source_session_id or "",
                    "metadata": str(entity.metadata),
                },
            )

        try:
            await self._run_sync(_insert)
        except Exception as e:
            raise StorageError(f"Failed to create entity: {e}") from e

    async def get_entity(self, entity_id: str) -> Entity | None:
        conn = self._conn
        assert conn is not None

        def _query():
            result = conn.execute(
                "MATCH (e:Entity) WHERE e.id = $id RETURN e",
                {"id": entity_id},
            )
            rows = result.get_as_df()
            if rows.empty:
                return None
            row = rows.iloc[0]
            props = row["e"]
            return Entity(
                id=props["id"],
                tenant_id=props["tenant_id"],
                user_id=props["user_id"],
                name=props["name"],
                entity_type=props["entity_type"],
                summary=props["summary"],
                confidence=props["confidence"],
                created_at=props["created_at"],
                last_referenced_at=props["last_referenced_at"],
                source_session_id=props.get("source_session_id") or None,
            )

        return await self._run_sync(_query)

    async def find_similar_entities(
        self, name: str, entity_type: str, user_id: str, tenant_id: str
    ) -> list[Entity]:
        conn = self._conn
        assert conn is not None

        def _query():
            result = conn.execute(
                """
                MATCH (e:Entity)
                WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
                  AND e.entity_type = $entity_type
                RETURN e
                """,
                {
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "entity_type": entity_type,
                },
            )
            rows = result.get_as_df()
            entities = []
            for _, row in rows.iterrows():
                props = row["e"]
                entities.append(Entity(
                    id=props["id"],
                    tenant_id=props["tenant_id"],
                    user_id=props["user_id"],
                    name=props["name"],
                    entity_type=props["entity_type"],
                    summary=props["summary"],
                    confidence=props["confidence"],
                    created_at=props["created_at"],
                    last_referenced_at=props["last_referenced_at"],
                    source_session_id=props.get("source_session_id") or None,
                ))
            return entities

        return await self._run_sync(_query)

    async def update_entity_reference(self, entity_id: str) -> None:
        conn = self._conn
        assert conn is not None

        def _update():
            conn.execute(
                """
                MATCH (e:Entity) WHERE e.id = $id
                SET e.last_referenced_at = $now
                """,
                {"id": entity_id, "now": datetime.utcnow()},
            )

        await self._run_sync(_update)

    async def create_relationship(self, rel: Relationship) -> None:
        conn = self._conn
        assert conn is not None

        def _insert():
            conn.execute(
                """
                MATCH (a:Entity), (b:Entity)
                WHERE a.id = $from_id AND b.id = $to_id
                CREATE (a)-[r:Rel {
                    id: $id, rel_type: $rel_type, summary: $summary,
                    confidence: $confidence, valid_from: $valid_from,
                    invalid_from: $invalid_from,
                    source_session_id: $source_session_id,
                    source_message_idx: $source_message_idx,
                    reasoning: $reasoning, metadata: $metadata
                }]->(b)
                """,
                {
                    "from_id": rel.from_entity_id,
                    "to_id": rel.to_entity_id,
                    "id": rel.id,
                    "rel_type": rel.rel_type.value if isinstance(rel.rel_type, RelType) else rel.rel_type,
                    "summary": rel.summary,
                    "confidence": rel.confidence,
                    "valid_from": rel.valid_from,
                    "invalid_from": rel.invalid_from,
                    "source_session_id": rel.source_session_id or "",
                    "source_message_idx": rel.source_message_idx or 0,
                    "reasoning": rel.reasoning,
                    "metadata": str(rel.metadata),
                },
            )

        try:
            await self._run_sync(_insert)
        except Exception as e:
            raise StorageError(f"Failed to create relationship: {e}") from e

    async def invalidate_relationship(self, rel_id: str, invalid_from: Any) -> None:
        conn = self._conn
        assert conn is not None

        def _update():
            conn.execute(
                """
                MATCH ()-[r:Rel]->() WHERE r.id = $id
                SET r.invalid_from = $invalid_from
                """,
                {"id": rel_id, "invalid_from": invalid_from},
            )

        await self._run_sync(_update)

    async def get_active_relationships(self, entity_id: str) -> list[Relationship]:
        conn = self._conn
        assert conn is not None

        def _query():
            result = conn.execute(
                """
                MATCH (a:Entity)-[r:Rel]->(b:Entity)
                WHERE a.id = $id AND r.invalid_from IS NULL
                RETURN r, b.id AS to_id, a.id AS from_id
                """,
                {"id": entity_id},
            )
            rows = result.get_as_df()
            rels = []
            for _, row in rows.iterrows():
                props = row["r"]
                rels.append(Relationship(
                    id=props["id"],
                    from_entity_id=row["from_id"],
                    to_entity_id=row["to_id"],
                    rel_type=props["rel_type"],
                    summary=props["summary"],
                    confidence=props["confidence"],
                    valid_from=props["valid_from"],
                    invalid_from=props.get("invalid_from"),
                    source_session_id=props.get("source_session_id") or None,
                    reasoning=props.get("reasoning", ""),
                ))
            return rels

        return await self._run_sync(_query)

    async def find_active_relationship(
        self, from_id: str, to_id: str, rel_type: str
    ) -> Relationship | None:
        conn = self._conn
        assert conn is not None

        def _query():
            result = conn.execute(
                """
                MATCH (a:Entity)-[r:Rel]->(b:Entity)
                WHERE a.id = $from_id AND b.id = $to_id
                  AND r.rel_type = $rel_type AND r.invalid_from IS NULL
                RETURN r, a.id AS from_id, b.id AS to_id
                ORDER BY r.valid_from DESC
                LIMIT 1
                """,
                {"from_id": from_id, "to_id": to_id, "rel_type": rel_type},
            )
            rows = result.get_as_df()
            if rows.empty:
                return None
            row = rows.iloc[0]
            props = row["r"]
            return Relationship(
                id=props["id"],
                from_entity_id=row["from_id"],
                to_entity_id=row["to_id"],
                rel_type=props["rel_type"],
                summary=props["summary"],
                confidence=props["confidence"],
                valid_from=props["valid_from"],
                invalid_from=props.get("invalid_from"),
                source_session_id=props.get("source_session_id") or None,
                reasoning=props.get("reasoning", ""),
            )

        return await self._run_sync(_query)

    async def list_entities(
        self, user_id: str, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[Entity]:
        conn = self._conn
        assert conn is not None

        def _query():
            result = conn.execute(
                """
                MATCH (e:Entity)
                WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
                RETURN e
                ORDER BY e.last_referenced_at DESC
                SKIP $offset LIMIT $limit
                """,
                {"user_id": user_id, "tenant_id": tenant_id, "offset": offset, "limit": limit},
            )
            rows = result.get_as_df()
            entities = []
            for _, row in rows.iterrows():
                props = row["e"]
                entities.append(Entity(
                    id=props["id"],
                    tenant_id=props["tenant_id"],
                    user_id=props["user_id"],
                    name=props["name"],
                    entity_type=props["entity_type"],
                    summary=props["summary"],
                    confidence=props["confidence"],
                    created_at=props["created_at"],
                    last_referenced_at=props["last_referenced_at"],
                ))
            return entities

        return await self._run_sync(_query)

    async def get_history(
        self, user_id: str, entity_name: str | None, tenant_id: str
    ) -> list[MemoryVersion]:
        conn = self._conn
        assert conn is not None

        def _query():
            if entity_name:
                result = conn.execute(
                    """
                    MATCH (a:Entity)-[r:Rel]->(b:Entity)
                    WHERE a.user_id = $user_id AND a.tenant_id = $tenant_id
                      AND (a.name CONTAINS $name OR b.name CONTAINS $name)
                    RETURN a.name AS entity_name, r.summary AS summary,
                           r.rel_type AS rel_type, r.valid_from AS valid_from,
                           r.invalid_from AS invalid_from
                    ORDER BY r.valid_from ASC
                    """,
                    {"user_id": user_id, "tenant_id": tenant_id, "name": entity_name},
                )
            else:
                result = conn.execute(
                    """
                    MATCH (a:Entity)-[r:Rel]->(b:Entity)
                    WHERE a.user_id = $user_id AND a.tenant_id = $tenant_id
                    RETURN a.name AS entity_name, r.summary AS summary,
                           r.rel_type AS rel_type, r.valid_from AS valid_from,
                           r.invalid_from AS invalid_from
                    ORDER BY r.valid_from ASC
                    """,
                    {"user_id": user_id, "tenant_id": tenant_id},
                )
            rows = result.get_as_df()
            versions = []
            for _, row in rows.iterrows():
                versions.append(MemoryVersion(
                    entity_name=row["entity_name"],
                    relationship_summary=row["summary"],
                    rel_type=row["rel_type"],
                    valid_from=row["valid_from"],
                    invalid_from=row.get("invalid_from"),
                    was_active=row.get("invalid_from") is None,
                ))
            return versions

        return await self._run_sync(_query)

    async def execute_cypher(self, query: str, params: dict | None = None) -> Any:
        """Execute a raw Cypher query (for graph search)."""
        conn = self._conn
        assert conn is not None

        def _query():
            result = conn.execute(query, params or {})
            return result.get_as_df()

        return await self._run_sync(_query)

    async def delete_entity(self, entity_id: str) -> None:
        conn = self._conn
        assert conn is not None

        def _delete():
            # Delete relationships first, then entity
            conn.execute(
                "MATCH (a:Entity)-[r:Rel]->() WHERE a.id = $id DELETE r",
                {"id": entity_id},
            )
            conn.execute(
                "MATCH ()-[r:Rel]->(b:Entity) WHERE b.id = $id DELETE r",
                {"id": entity_id},
            )
            conn.execute(
                "MATCH (e:Entity) WHERE e.id = $id DELETE e",
                {"id": entity_id},
            )

        await self._run_sync(_delete)

    async def delete_user_data(self, user_id: str, tenant_id: str) -> int:
        conn = self._conn
        assert conn is not None

        def _delete():
            # Count entities first
            result = conn.execute(
                """
                MATCH (e:Entity)
                WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
                RETURN count(e) AS cnt
                """,
                {"user_id": user_id, "tenant_id": tenant_id},
            )
            df = result.get_as_df()
            count = int(df.iloc[0]["cnt"]) if not df.empty else 0

            # Delete relationships
            conn.execute(
                """
                MATCH (a:Entity)-[r:Rel]->()
                WHERE a.user_id = $user_id AND a.tenant_id = $tenant_id
                DELETE r
                """,
                {"user_id": user_id, "tenant_id": tenant_id},
            )
            conn.execute(
                """
                MATCH ()-[r:Rel]->(b:Entity)
                WHERE b.user_id = $user_id AND b.tenant_id = $tenant_id
                DELETE r
                """,
                {"user_id": user_id, "tenant_id": tenant_id},
            )
            # Delete entities
            conn.execute(
                """
                MATCH (e:Entity)
                WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
                DELETE e
                """,
                {"user_id": user_id, "tenant_id": tenant_id},
            )
            return count

        return await self._run_sync(_delete)

    async def close(self) -> None:
        self._conn = None
        self._db = None
