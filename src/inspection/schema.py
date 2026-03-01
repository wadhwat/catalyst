from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.report.schema import Report


class YoloDetection(BaseModel):
    detection_id: int
    class_name: str
    confidence: float
    bbox: List[float] = Field(
        ..., description="Normalized [cx, cy, w, h] in 0-1 range"
    )
    frame_index: int


class MappedDefect(BaseModel):
    detection_id: int
    checklist_item: str
    defect_type: str
    confirmed: bool = True
    severity: str = Field(
        ..., description="Minor | Moderate | Critical"
    )
    description: str
    bbox: List[float]


class VlmFrameResult(BaseModel):
    frame_index: int
    mapped_defects: List[MappedDefect] = Field(default_factory=list)
    error: Optional[str] = None


class Finding(BaseModel):
    checklist_item: str
    defect_type: str
    severity: str
    description: str
    bbox: List[float]
    confidence: float
    frame_index: int
    timestamp_sec: Optional[float] = None
    needs_human_review: bool = False


class ModelVersions(BaseModel):
    yolo_weights: str
    openai_model: str


class ProcessingStats(BaseModel):
    frame_count: int
    frames_with_detections: int
    yolo_ms: float
    vlm_ms: float
    aggregation_ms: float
    total_ms: float


class FrameError(BaseModel):
    frame_index: int
    stage: str
    message: str


class InferenceResponse(BaseModel):
    inspection_id: str
    model_versions: ModelVersions
    findings: List[Finding]
    report: Report
    processing_stats: ProcessingStats
    errors: List[FrameError] = Field(default_factory=list)
