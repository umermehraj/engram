"""Abstract base classes for storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from engram.types import Entity, Relationship, MemoryVersion


class GraphBackend(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def create_entity(self, entity: Entity) -> None: ...

    @abstractmethod
    async def get_entity(self, entity_id: str) -> Entity | None: ...

    @abstractmethod
    async def find_similar_entities(
        self, name: str, entity_type: str, user_id: str, tenant_id: str
    ) -> list[Entity]: ...

    @abstractmethod
    async def update_entity_reference(self, entity_id: str) -> None: ...

    @abstractmethod
    async def create_relationship(self, rel: Relationship) -> None: ...

    @abstractmethod
    async def invalidate_relationship(self, rel_id: str, invalid_from: Any) -> None: ...

    @abstractmethod
    async def get_active_relationships(self, entity_id: str) -> list[Relationship]: ...

    @abstractmethod
    async def find_active_relationship(
        self, from_id: str, to_id: str, rel_type: str
    ) -> Relationship | None: ...

    @abstractmethod
    async def list_entities(
        self, user_id: str, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[Entity]: ...

    @abstractmethod
    async def get_history(
        self, user_id: str, entity_name: str | None, tenant_id: str
    ) -> list[MemoryVersion]: ...

    @abstractmethod
    async def delete_entity(self, entity_id: str) -> None: ...

    @abstractmethod
    async def delete_user_data(self, user_id: str, tenant_id: str) -> int: ...

    @abstractmethod
    async def close(self) -> None: ...


class VectorBackend(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def upsert(
        self, entity_id: str, user_id: str, tenant_id: str,
        embedding: list[float], summary: str, entity_type: str,
    ) -> None: ...

    @abstractmethod
    async def search(
        self, query_embedding: list[float], user_id: str, tenant_id: str, top_k: int = 50,
    ) -> list[tuple[str, float]]: ...

    @abstractmethod
    async def delete_by_entity_id(self, entity_id: str) -> None: ...

    @abstractmethod
    async def delete_user_data(self, user_id: str, tenant_id: str) -> int: ...

    @abstractmethod
    async def close(self) -> None: ...


class MetadataBackend(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def delete_user_data(self, user_id: str, tenant_id: str) -> int: ...

    @abstractmethod
    async def close(self) -> None: ...
