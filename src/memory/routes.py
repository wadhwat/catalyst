from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.routes import require_user
from src.memory.schema import MemoryAddRequest, MemorySearchRequest, MemorySearchResponse
from src.memory.supermemory_client import SupermemoryClient

router = APIRouter(prefix='/memories', tags=['memories'])
memory_client = SupermemoryClient()


def _merge_user_tags(user_id: int, tags: list[str]) -> list[str]:
    merged = list(tags)
    tag = f'user:{user_id}'
    if tag not in merged:
        merged.append(tag)
    return merged


def _ensure_enabled() -> None:
    if not memory_client.api_key or not memory_client.base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Supermemory is not configured',
        )


@router.post('/add')
def add_memory(payload: MemoryAddRequest, user=Depends(require_user)) -> dict:
    _ensure_enabled()
    tags = _merge_user_tags(user.id, payload.tags)
    created = memory_client.create_memory(
        kind=payload.kind,
        content=payload.content,
        tags=tags,
        metadata=payload.metadata,
    )
    if not created:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Failed to create memory')
    return created


@router.post('/search', response_model=MemorySearchResponse)
def search_memories(payload: MemorySearchRequest, user=Depends(require_user)) -> MemorySearchResponse:
    _ensure_enabled()
    tags = _merge_user_tags(user.id, payload.tags)
    results = memory_client.search_memories(
        query=payload.query,
        tags=tags,
        limit=payload.limit,
        metadata=payload.metadata,
    )
    return MemorySearchResponse(results=results)
