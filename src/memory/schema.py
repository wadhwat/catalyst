from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MemoryReference(BaseModel):
    filename: str
    sha256: str


class ItemSummary(BaseModel):
    id: str
    status: str
    notes: Optional[str] = None


class VehicleProfile(BaseModel):
    vin: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    nickname: Optional[str] = None


class SessionSummary(BaseModel):
    vin: str
    client_trace_id: str
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    summary_status: str
    items: List[ItemSummary]
    references: List[MemoryReference] = Field(default_factory=list)


class EngineerNote(BaseModel):
    vin: str
    author: Optional[str] = None
    note: str
    observed_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryAddRequest(BaseModel):
    kind: str
    content: dict
    tags: list[str] = Field(default_factory=list)
    metadata: Optional[dict] = None


class MemorySearchRequest(BaseModel):
    query: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    limit: int = 5
    metadata: Optional[dict] = None


class MemorySearchResponse(BaseModel):
    results: list[dict]
