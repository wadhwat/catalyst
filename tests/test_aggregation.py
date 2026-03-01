from __future__ import annotations

import pytest

from src.inspection.aggregation import aggregate_findings, compute_iou
from src.inspection.schema import MappedDefect, VlmFrameResult


class TestComputeIou:
    def test_identical_boxes(self):
        bbox = [0.5, 0.5, 0.2, 0.2]
        assert abs(compute_iou(bbox, bbox) - 1.0) < 1e-6

    def test_no_overlap(self):
        a = [0.1, 0.1, 0.1, 0.1]
        b = [0.9, 0.9, 0.1, 0.1]
        assert compute_iou(a, b) == 0.0

    def test_partial_overlap(self):
        a = [0.5, 0.5, 0.4, 0.4]
        b = [0.6, 0.6, 0.4, 0.4]
        iou = compute_iou(a, b)
        assert 0.0 < iou < 1.0

    def test_contained_box(self):
        outer = [0.5, 0.5, 0.8, 0.8]
        inner = [0.5, 0.5, 0.2, 0.2]
        iou = compute_iou(outer, inner)
        expected = (0.2 * 0.2) / (0.8 * 0.8)
        assert abs(iou - expected) < 1e-6

    def test_zero_area_box(self):
        a = [0.5, 0.5, 0.0, 0.0]
        b = [0.5, 0.5, 0.1, 0.1]
        assert compute_iou(a, b) == 0.0

    def test_symmetry(self):
        a = [0.3, 0.4, 0.2, 0.3]
        b = [0.4, 0.5, 0.2, 0.3]
        assert abs(compute_iou(a, b) - compute_iou(b, a)) < 1e-9


def _make_defect(
    det_id: int = 1,
    checklist: str = "Boom, cylinders",
    defect_type: str = "corrosion",
    severity: str = "Minor",
    bbox: list[float] | None = None,
) -> MappedDefect:
    return MappedDefect(
        detection_id=det_id,
        checklist_item=checklist,
        defect_type=defect_type,
        confirmed=True,
        severity=severity,
        description=f"Test {defect_type}",
        bbox=bbox or [0.5, 0.5, 0.1, 0.1],
    )


class TestAggregate:
    def test_empty_input(self):
        findings, ms = aggregate_findings([])
        assert findings == []
        assert ms >= 0

    def test_single_finding_passthrough(self):
        result = VlmFrameResult(
            frame_index=0,
            mapped_defects=[_make_defect()],
        )
        findings, _ = aggregate_findings([result])
        assert len(findings) == 1
        assert findings[0].checklist_item == "Boom, cylinders"

    def test_merges_same_item_adjacent_frames(self):
        d1 = _make_defect(det_id=1, bbox=[0.5, 0.5, 0.1, 0.1])
        d2 = _make_defect(det_id=1, bbox=[0.51, 0.51, 0.1, 0.1])
        r1 = VlmFrameResult(frame_index=0, mapped_defects=[d1])
        r2 = VlmFrameResult(frame_index=1, mapped_defects=[d2])
        findings, _ = aggregate_findings([r1, r2])
        assert len(findings) == 1

    def test_no_merge_different_checklist(self):
        d1 = _make_defect(det_id=1, checklist="Boom, cylinders")
        d2 = _make_defect(det_id=1, checklist="Radiator")
        r1 = VlmFrameResult(frame_index=0, mapped_defects=[d1])
        r2 = VlmFrameResult(frame_index=1, mapped_defects=[d2])
        findings, _ = aggregate_findings([r1, r2])
        assert len(findings) == 2

    def test_no_merge_distant_frames(self):
        d1 = _make_defect(det_id=1, bbox=[0.5, 0.5, 0.1, 0.1])
        d2 = _make_defect(det_id=1, bbox=[0.5, 0.5, 0.1, 0.1])
        r1 = VlmFrameResult(frame_index=0, mapped_defects=[d1])
        r2 = VlmFrameResult(frame_index=10, mapped_defects=[d2])
        findings, _ = aggregate_findings([r1, r2])
        assert len(findings) == 2

    def test_no_merge_low_iou(self):
        d1 = _make_defect(det_id=1, bbox=[0.1, 0.1, 0.1, 0.1])
        d2 = _make_defect(det_id=1, bbox=[0.9, 0.9, 0.1, 0.1])
        r1 = VlmFrameResult(frame_index=0, mapped_defects=[d1])
        r2 = VlmFrameResult(frame_index=1, mapped_defects=[d2])
        findings, _ = aggregate_findings([r1, r2])
        assert len(findings) == 2

    def test_keeps_worst_severity(self):
        d1 = _make_defect(det_id=1, severity="Minor", bbox=[0.5, 0.5, 0.1, 0.1])
        d2 = _make_defect(det_id=1, severity="Critical", bbox=[0.5, 0.5, 0.1, 0.1])
        r1 = VlmFrameResult(frame_index=0, mapped_defects=[d1])
        r2 = VlmFrameResult(frame_index=1, mapped_defects=[d2])
        findings, _ = aggregate_findings([r1, r2])
        assert len(findings) == 1
        assert findings[0].severity == "Critical"

    def test_invalid_checklist_normalized(self):
        d = _make_defect(checklist="Nonexistent item")
        result = VlmFrameResult(frame_index=0, mapped_defects=[d])
        findings, _ = aggregate_findings([result])
        assert findings[0].checklist_item == "Overall machine"

    def test_timestamps_applied(self):
        d = _make_defect()
        result = VlmFrameResult(frame_index=2, mapped_defects=[d])
        findings, _ = aggregate_findings([result], frame_timestamps={2: 4.0})
        assert findings[0].timestamp_sec == 4.0

    def test_unconfirmed_needs_review(self):
        d = MappedDefect(
            detection_id=1,
            checklist_item="Boom, cylinders",
            defect_type="corrosion",
            confirmed=False,
            severity="Minor",
            description="Unclear",
            bbox=[0.5, 0.5, 0.1, 0.1],
        )
        result = VlmFrameResult(frame_index=0, mapped_defects=[d])
        findings, _ = aggregate_findings([result])
        assert findings[0].needs_human_review is True
