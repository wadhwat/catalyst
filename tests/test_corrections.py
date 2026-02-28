from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.corrections.schema import (
    CorrectionCreate,
    CorrectionResponse,
    CorrectionSearchRequest,
    CorrectionSearchResponse,
)


def test_correction_create_model() -> None:
    """Test CorrectionCreate validation."""
    correction = CorrectionCreate(
        item_id='tires_wheels',
        vin='CAT320-001',
        client_trace_id='abc123',
        original_status='PASS',
        original_score=0.15,
        original_confidence=0.92,
        original_reasoning='Tires look good',
        corrected_status='MONITOR',
        corrected_score=0.45,
        correction_notes='Visible sidewall bulge on front left',
        frame_sha256='abcd1234',
        frame_filename='frame_001.jpg',
    )

    assert correction.item_id == 'tires_wheels'
    assert correction.corrected_status == 'MONITOR'
    assert correction.correction_notes == 'Visible sidewall bulge on front left'


def test_correction_create_notes_minimum() -> None:
    """Test correction notes minimum length validation."""
    with pytest.raises(ValueError):
        CorrectionCreate(
            item_id='tires_wheels',
            vin='CAT320-001',
            client_trace_id='abc123',
            original_status='PASS',
            original_score=0.15,
            original_confidence=0.92,
            corrected_status='MONITOR',
            corrected_score=0.45,
            correction_notes='Short',  # Less than 10 chars
            frame_sha256='abcd1234',
        )


def test_correction_response_model() -> None:
    """Test CorrectionResponse model."""
    response = CorrectionResponse(
        id='corr_123',
        item_id='tires_wheels',
        vin='CAT320-001',
        created_at=datetime.now(timezone.utc),
        original_status='PASS',
        original_score=0.15,
        corrected_status='MONITOR',
        corrected_score=0.45,
        correction_notes='Visible damage',
    )

    assert response.id == 'corr_123'
    assert response.original_status == 'PASS'
    assert response.corrected_status == 'MONITOR'


def test_correction_search_request() -> None:
    """Test search request validation."""
    # Default limit
    request = CorrectionSearchRequest()
    assert request.limit == 5

    # Custom limit
    request = CorrectionSearchRequest(item_id='tires_wheels', limit=10)
    assert request.item_id == 'tires_wheels'
    assert request.limit == 10

    # Max limit validation
    with pytest.raises(ValueError):
        CorrectionSearchRequest(limit=25)  # > 20


def test_correction_search_response() -> None:
    """Test search response model."""
    corrections = [
        CorrectionResponse(
            id='corr_1',
            item_id='tires_wheels',
            vin='CAT320-001',
            created_at=datetime.now(timezone.utc),
            original_status='PASS',
            original_score=0.15,
            corrected_status='FAIL',
            corrected_score=0.75,
            correction_notes='Missing lug nuts',
        ),
    ]

    response = CorrectionSearchResponse(corrections=corrections, total=1)
    assert len(response.corrections) == 1
    assert response.total == 1
