from __future__ import annotations

import logging
import time
from typing import List

from src.inspection.checklist import CHECKLIST_SET
from src.inspection.schema import Finding, VlmFrameResult

logger = logging.getLogger(__name__)

_IOU_MERGE_THRESHOLD = 0.5
_FRAME_ADJACENCY_WINDOW = 3


def compute_iou(bbox_a: List[float], bbox_b: List[float]) -> float:
    """Compute IoU between two [cx, cy, w, h] normalized bboxes."""
    ax1 = bbox_a[0] - bbox_a[2] / 2
    ay1 = bbox_a[1] - bbox_a[3] / 2
    ax2 = bbox_a[0] + bbox_a[2] / 2
    ay2 = bbox_a[1] + bbox_a[3] / 2

    bx1 = bbox_b[0] - bbox_b[2] / 2
    by1 = bbox_b[1] - bbox_b[3] / 2
    bx2 = bbox_b[0] + bbox_b[2] / 2
    by2 = bbox_b[1] + bbox_b[3] / 2

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = bbox_a[2] * bbox_a[3]
    area_b = bbox_b[2] * bbox_b[3]
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def _normalize_checklist_item(item: str) -> str:
    if item in CHECKLIST_SET:
        return item
    return "Overall machine"


def _severity_rank(severity: str) -> int:
    return {"Minor": 0, "Moderate": 1, "Critical": 2}.get(severity, 0)


def aggregate_findings(
    vlm_results: List[VlmFrameResult],
    frame_timestamps: dict[int, float] | None = None,
) -> tuple[List[Finding], float]:
    """
    Deduplicate and merge VLM findings across frames.

    Merging criteria: same checklist_item + same defect_type + bbox IoU > threshold
    across frames within the adjacency window.
    """
    t0 = time.perf_counter()
    frame_timestamps = frame_timestamps or {}

    raw_findings: List[Finding] = []
    for result in vlm_results:
        for defect in result.mapped_defects:
            checklist_item = _normalize_checklist_item(defect.checklist_item)
            needs_review = not defect.confirmed or max(defect.bbox) == 0
            raw_findings.append(
                Finding(
                    checklist_item=checklist_item,
                    defect_type=defect.defect_type,
                    severity=defect.severity,
                    description=defect.description,
                    bbox=defect.bbox,
                    confidence=0.0,
                    frame_index=result.frame_index,
                    timestamp_sec=frame_timestamps.get(result.frame_index),
                    needs_human_review=needs_review,
                )
            )

    merged: List[Finding] = []
    used = [False] * len(raw_findings)

    for i, finding in enumerate(raw_findings):
        if used[i]:
            continue
        used[i] = True
        best = finding

        for j in range(i + 1, len(raw_findings)):
            if used[j]:
                continue
            other = raw_findings[j]
            if (
                other.checklist_item != best.checklist_item
                or other.defect_type != best.defect_type
            ):
                continue
            if abs(other.frame_index - best.frame_index) > _FRAME_ADJACENCY_WINDOW:
                continue
            if compute_iou(best.bbox, other.bbox) < _IOU_MERGE_THRESHOLD:
                continue

            used[j] = True
            if _severity_rank(other.severity) > _severity_rank(best.severity):
                best = Finding(
                    checklist_item=best.checklist_item,
                    defect_type=best.defect_type,
                    severity=other.severity,
                    description=other.description,
                    bbox=other.bbox,
                    confidence=max(best.confidence, other.confidence),
                    frame_index=other.frame_index,
                    timestamp_sec=other.timestamp_sec,
                    needs_human_review=best.needs_human_review or other.needs_human_review,
                )
            else:
                best = best.model_copy(
                    update={
                        "confidence": max(best.confidence, other.confidence),
                        "needs_human_review": best.needs_human_review or other.needs_human_review,
                    }
                )

        merged.append(best)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "Aggregation: %d raw -> %d merged findings, %.1f ms",
        len(raw_findings),
        len(merged),
        elapsed_ms,
    )
    return merged, elapsed_ms
