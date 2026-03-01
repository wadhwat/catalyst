from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ReportItem(BaseModel):
    id: str
    status: str
    score: Optional[float] = None
    notes: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    recommended_parts: List[str] = Field(
        default_factory=list,
        description="Part numbers recommended for fixing defects (from inventory)",
    )


class ReportSummary(BaseModel):
    status: str
    notes: Optional[str] = None


class Report(BaseModel):
    summary: ReportSummary
    items: List[ReportItem]
