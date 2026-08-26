"""User management endpoints (GDPR deletion)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engram.api.auth import get_client_from_request
from engram.api.main import get_client

router = APIRouter()


@router.delete("/users/{user_id}/memories")
async def delete_user_memories(
    user_id: str,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    count = await client.delete_user(user_id=user_id, tenant_id=tenant_id)
    return {"success": True, "user_id": user_id, "records_deleted": count}
