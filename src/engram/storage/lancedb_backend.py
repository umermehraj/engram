"""LanceDB embedded vector store backend."""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import partial
from typing import Any

import lancedb
import pyarrow as pa

from engram.config import EngramConfig
from engram.exceptions import StorageError
from engram.storage.base import VectorBackend


class LanceDBBackend(VectorBackend):
    def __init__(self, config: EngramConfig) -> None:
        self.config = config
        self._db: Any = None
        self._table: Any = None
        self._table_name = "entities"

    async def initialize(self) -> None:
        self.config.lancedb_path.mkdir(parents=True, exist_ok=True)

        def _init():
            self._db = lancedb.connect(str(self.config.lancedb_path))
            # Create or open table
            try:
                self._table = self._db.open_table(self._table_name)
            except Exception:
                # Create with schema
                schema = pa.schema([
                    pa.field("id", pa.string()),
                    pa.field("entity_id", pa.string()),
                    pa.field("user_id", pa.string()),
                    pa.field("tenant_id", pa.string()),
                    pa.field("summary", pa.string()),
                    pa.field("entity_type", pa.string()),
                    pa.field("created_at", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), self.config.embedding_dim)),
                ])
                self._table = self._db.create_table(
                    self._table_name,
                    schema=schema,
                )

        await asyncio.get_event_loop().run_in_executor(None, _init)

    async def upsert(
        self,
        entity_id: str,
        user_id: str,
        tenant_id: str,
        embedding: list[float],
        summary: str,
        entity_type: str,
    ) -> None:
        table = self._table
        if table is None:
            raise StorageError("LanceDB not initialized")

        def _upsert():
            data = [{
                "id": entity_id,
                "entity_id": entity_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "summary": summary,
                "entity_type": entity_type,
                "created_at": datetime.utcnow().isoformat(),
                "vector": embedding,
            }]
            # Try to delete existing first, then add
            try:
                table.delete(f"entity_id = '{entity_id}'")
            except Exception:
                pass
            table.add(data)

        try:
            await asyncio.get_event_loop().run_in_executor(None, _upsert)
        except Exception as e:
            raise StorageError(f"Failed to upsert vector: {e}") from e

    async def search(
        self,
        query_embedding: list[float],
        user_id: str,
        tenant_id: str,
        top_k: int = 50,
    ) -> list[tuple[str, float]]:
        """Return list of (entity_id, distance) sorted by relevance."""
        table = self._table
        if table is None:
            raise StorageError("LanceDB not initialized")

        def _search():
            try:
                results = (
                    table.search(query_embedding)
                    .where(f"user_id = '{user_id}' AND tenant_id = '{tenant_id}'")
                    .limit(top_k)
                    .to_list()
                )
                return [(r["entity_id"], float(r["_distance"])) for r in results]
            except Exception:
                return []

        return await asyncio.get_event_loop().run_in_executor(None, _search)

    async def delete_by_entity_id(self, entity_id: str) -> None:
        table = self._table
        if table is None:
            return

        def _delete():
            try:
                table.delete(f"entity_id = '{entity_id}'")
            except Exception:
                pass

        await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def delete_user_data(self, user_id: str, tenant_id: str) -> int:
        table = self._table
        if table is None:
            return 0

        def _delete():
            try:
                # Count before delete
                df = table.to_pandas()
                mask = (df["user_id"] == user_id) & (df["tenant_id"] == tenant_id)
                count = int(mask.sum())
                if count > 0:
                    table.delete(f"user_id = '{user_id}' AND tenant_id = '{tenant_id}'")
                return count
            except Exception:
                return 0

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def close(self) -> None:
        self._table = None
        self._db = None
