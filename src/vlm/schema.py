from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Result from VLM classification."""

    item_id: str
    status: str  # PASS, MONITOR, FAIL, or UNKNOWN
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
