"""Memory CRUD endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from engram.api.auth import get_client_from_request
from engram.api.main import get_client
from engram.types import AddMemoryRequest, AddMemoryResponse

router = APIRouter()


@router.post("/memories", response_model=AddMemoryResponse)
async def add_memories(
    request: AddMemoryRequest,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    return await client.add(
        messages=request.messages,
        text=request.text,
        user_id=request.user_id,
        session_id=request.session_id,
        metadata=request.metadata,
        tenant_id=tenant_id,
    )


@router.get("/memories")
async def list_memories(
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    entities = await client.get_all(
        user_id=user_id, tenant_id=tenant_id, limit=limit, offset=offset
    )
    return {"memories": [e.model_dump() for e in entities], "count": len(entities)}


@router.get("/memories/history")
async def memory_history(
    user_id: str,
    entity_name: str | None = None,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    versions = await client.history(
        user_id=user_id, entity_name=entity_name, tenant_id=tenant_id
    )
    return {"history": [v.model_dump() for v in versions]}


@router.get("/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    assert client._graph is not None
    entity = await client._graph.get_entity(memory_id)
    if entity is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Memory not found")
    relationships = await client._graph.get_active_relationships(memory_id)
    return {
        "entity": entity.model_dump(),
        "relationships": [r.model_dump() for r in relationships],
    }


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    success = await client.delete(memory_id=memory_id)
    return {"success": success, "memory_id": memory_id}
