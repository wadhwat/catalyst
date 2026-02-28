from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.routes import require_user
from src.auth.schema import ProfileResponse
from src.corrections.schema import (
    CorrectionCreate,
    CorrectionResponse,
    CorrectionSearchRequest,
    CorrectionSearchResponse,
)
from src.memory.supermemory_client import SupermemoryClient

router = APIRouter(prefix='/corrections', tags=['corrections'])
memory_client = SupermemoryClient()


def _ensure_enabled() -> None:
    if not memory_client.api_key or not memory_client.base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Supermemory is not configured',
        )


@router.post('', response_model=CorrectionResponse)
def create_correction(
    payload: CorrectionCreate,
    user: ProfileResponse = Depends(require_user),
) -> CorrectionResponse:
    """Store a correction for a VLM classification."""
    _ensure_enabled()

    correction_id = uuid.uuid4().hex[:12]
    created_at = datetime.now(timezone.utc)

    # Build Supermemory content
    content = {
        'id': correction_id,
        'item_id': payload.item_id,
        'vin': payload.vin,
        'client_trace_id': payload.client_trace_id,
        'user_id': user.id,
        'user_email': user.email,
        'created_at': created_at.isoformat(),
        # Original prediction
        'original': {
            'status': payload.original_status,
            'score': payload.original_score,
            'confidence': payload.original_confidence,
            'reasoning': payload.original_reasoning,
        },
        # Correction
        'corrected': {
            'status': payload.corrected_status,
            'score': payload.corrected_score,
        },
        'correction_notes': payload.correction_notes,
        # Reference
        'frame_sha256': payload.frame_sha256,
        'frame_filename': payload.frame_filename,
    }

    # Build tags for efficient querying
    tags = [
        f'user:{user.id}',
        f'vin:{payload.vin}',
        f'item:{payload.item_id}',
        'kind:classification_correction',
    ]

    result = memory_client.create_memory(
        kind='classification_correction',
        content=content,
        tags=tags,
        metadata={
            'vin': payload.vin,
            'item_id': payload.item_id,
            'client_trace_id': payload.client_trace_id,
        },
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Failed to store correction',
        )

    return CorrectionResponse(
        id=correction_id,
        item_id=payload.item_id,
        vin=payload.vin,
        created_at=created_at,
        original_status=payload.original_status,
        original_score=payload.original_score,
        corrected_status=payload.corrected_status,
        corrected_score=payload.corrected_score,
        correction_notes=payload.correction_notes,
    )


@router.post('/search', response_model=CorrectionSearchResponse)
def search_corrections(
    payload: CorrectionSearchRequest,
    user: ProfileResponse = Depends(require_user),
) -> CorrectionSearchResponse:
    """Search for past corrections."""
    _ensure_enabled()

    tags = [f'user:{user.id}', 'kind:classification_correction']

    if payload.item_id:
        tags.append(f'item:{payload.item_id}')
    if payload.vin:
        tags.append(f'vin:{payload.vin}')

    results = memory_client.search_memories(
        tags=tags,
        limit=payload.limit,
    )

    corrections = []
    for result in results:
        content = result.get('content', {})
        try:
            corrections.append(
                CorrectionResponse(
                    id=content.get('id', ''),
                    item_id=content.get('item_id', ''),
                    vin=content.get('vin', ''),
                    created_at=datetime.fromisoformat(
                        content.get('created_at', datetime.now(timezone.utc).isoformat())
                    ),
                    original_status=content.get('original', {}).get('status', ''),
                    original_score=content.get('original', {}).get('score', 0.0),
                    corrected_status=content.get('corrected', {}).get('status', ''),
                    corrected_score=content.get('corrected', {}).get('score', 0.0),
                    correction_notes=content.get('correction_notes', ''),
                )
            )
        except Exception:
            # Skip malformed entries
            continue

    return CorrectionSearchResponse(
        corrections=corrections,
        total=len(corrections),
    )
