from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CorrectionCreate(BaseModel):
    """Request to create a correction."""

    item_id: str
    vin: str
    client_trace_id: str

    # Original VLM prediction
    original_status: str
    original_score: float
    original_confidence: float
    original_reasoning: Optional[str] = None

    # Corrected values
    corrected_status: str
    corrected_score: float

    # Context
    correction_notes: str = Field(min_length=10)
    frame_sha256: str
    frame_filename: Optional[str] = None


class CorrectionResponse(BaseModel):
    """Response after creating a correction."""

    id: str
    item_id: str
    vin: str
    created_at: datetime

    original_status: str
    original_score: float
    corrected_status: str
    corrected_score: float
    correction_notes: str


class CorrectionSearchRequest(BaseModel):
    """Request to search corrections."""

    item_id: Optional[str] = None
    vin: Optional[str] = None
    limit: int = Field(default=5, le=20)


class CorrectionSearchResponse(BaseModel):
    """Response from correction search."""

    corrections: list[CorrectionResponse]
    total: int
