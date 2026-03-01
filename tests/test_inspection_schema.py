from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.inspection.checklist import CHECKLIST_ITEMS, CHECKLIST_SET
from src.inspection.schema import (
    Finding,
    FrameError,
    InferenceResponse,
    MappedDefect,
    ModelVersions,
    ProcessingStats,
    VlmFrameResult,
    YoloDetection,
)
from src.report.schema import Report, ReportItem, ReportSummary


class TestYoloDetection:
    def test_valid(self):
        d = YoloDetection(
            detection_id=1,
            class_name="corrosion",
            confidence=0.91,
            bbox=[0.5, 0.5, 0.1, 0.1],
            frame_index=0,
        )
        assert d.detection_id == 1
        assert d.bbox == [0.5, 0.5, 0.1, 0.1]

    def test_missing_bbox_raises(self):
        with pytest.raises(ValidationError):
            YoloDetection(
                detection_id=1,
                class_name="corrosion",
                confidence=0.91,
                frame_index=0,
            )


class TestMappedDefect:
    def test_valid(self):
        d = MappedDefect(
            detection_id=1,
            checklist_item="Boom, cylinders",
            defect_type="corrosion",
            confirmed=True,
            severity="Minor",
            description="Light surface rust on boom.",
            bbox=[0.3, 0.4, 0.1, 0.05],
        )
        assert d.severity == "Minor"

    def test_severity_values(self):
        for sev in ("Minor", "Moderate", "Critical"):
            d = MappedDefect(
                detection_id=1,
                checklist_item="Radiator",
                defect_type="corrosion",
                confirmed=True,
                severity=sev,
                description="Test",
                bbox=[0.0, 0.0, 0.1, 0.1],
            )
            assert d.severity == sev


class TestFinding:
    def test_defaults(self):
        f = Finding(
            checklist_item="Bucket/GET",
            defect_type="corrosion",
            severity="Moderate",
            description="Rust on bucket teeth",
            bbox=[0.2, 0.3, 0.1, 0.1],
            confidence=0.85,
            frame_index=3,
        )
        assert f.needs_human_review is False
        assert f.timestamp_sec is None


class TestChecklist:
    def test_no_duplicates_except_mirrors(self):
        seen = set()
        for item in CHECKLIST_ITEMS:
            if item == "Mirrors":
                continue
            assert item not in seen, f"Duplicate: {item}"
            seen.add(item)

    def test_key_items_present(self):
        assert "Bucket/GET" in CHECKLIST_SET
        assert "Overall machine" in CHECKLIST_SET
        assert "Overall cab interior" in CHECKLIST_SET
        assert "Boom, cylinders" in CHECKLIST_SET
        assert "Engine oil" in CHECKLIST_SET

    def test_at_least_30_items(self):
        assert len(CHECKLIST_ITEMS) >= 30


class TestInferenceResponse:
    def test_full_construction(self):
        resp = InferenceResponse(
            inspection_id="test-123",
            model_versions=ModelVersions(
                yolo_weights="custom_v1.pt",
                openai_model="gpt-4o",
            ),
            findings=[],
            report=Report(
                summary=ReportSummary(status="PASS", notes="All clear."),
                items=[],
            ),
            processing_stats=ProcessingStats(
                frame_count=5,
                frames_with_detections=2,
                yolo_ms=120.5,
                vlm_ms=3400.0,
                aggregation_ms=1.2,
                total_ms=3521.7,
            ),
            errors=[],
        )
        assert resp.inspection_id == "test-123"
        assert resp.errors == []
