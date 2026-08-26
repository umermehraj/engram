"""Search endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engram.api.auth import get_client_from_request
from engram.api.main import get_client
from engram.types import SearchRequest, SearchResponse

router = APIRouter()


@router.post("/memories/search", response_model=SearchResponse)
async def search_memories(
    request: SearchRequest,
    tenant_id: str = Depends(get_client_from_request),
):
    client = get_client()
    context = await client.search(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        top_k=request.top_k,
        token_budget=request.token_budget,
        mode=request.mode,
        tenant_id=tenant_id,
    )
    return SearchResponse(
        context=context.text,
        facts=context.facts,
        metadata=context.retrieval_metadata,
    )
