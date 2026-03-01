from __future__ import annotations

import logging
import os
import time
from typing import List

import numpy as np

from src.inspection.schema import YoloDetection

logger = logging.getLogger(__name__)

_model = None
_weights_name: str = ""


def _get_conf_threshold() -> float:
    try:
        return float(os.getenv("YOLO_CONF_THRESHOLD", "0.25"))
    except ValueError:
        return 0.25


def _load_model():
    global _model, _weights_name
    if _model is not None:
        return _model

    from ultralytics import YOLO

    weights_path = os.getenv("YOLO_WEIGHTS_PATH", "")
    if weights_path and os.path.isfile(weights_path):
        logger.info("Loading YOLO weights from %s", weights_path)
        _weights_name = os.path.basename(weights_path)
    else:
        if weights_path:
            logger.warning(
                "YOLO_WEIGHTS_PATH=%s not found, falling back to yolov8n.pt",
                weights_path,
            )
        else:
            logger.warning(
                "YOLO_WEIGHTS_PATH not set, falling back to yolov8n.pt (dev only)"
            )
        weights_path = "yolov8n.pt"
        _weights_name = "yolov8n.pt"

    _model = YOLO(weights_path)
    return _model


def get_weights_name() -> str:
    _load_model()
    return _weights_name


def detect_frame(
    image: np.ndarray,
    frame_index: int,
) -> List[YoloDetection]:
    """Run YOLO on a single frame, return detections with normalized bboxes."""
    model = _load_model()
    conf = _get_conf_threshold()

    results = model.predict(image, conf=conf, verbose=False)
    if not results:
        return []

    result = results[0]
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return []

    img_h, img_w = image.shape[:2]
    detections: List[YoloDetection] = []

    for i, box in enumerate(boxes):
        xyxy = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = xyxy
        cx = ((x1 + x2) / 2.0) / img_w
        cy = ((y1 + y2) / 2.0) / img_h
        w = (x2 - x1) / img_w
        h = (y2 - y1) / img_h

        cls_id = int(box.cls[0].item())
        cls_name = result.names.get(cls_id, f"class_{cls_id}")
        confidence = float(box.conf[0].item())

        detections.append(
            YoloDetection(
                detection_id=i + 1,
                class_name=cls_name,
                confidence=confidence,
                bbox=[round(cx, 4), round(cy, 4), round(w, 4), round(h, 4)],
                frame_index=frame_index,
            )
        )

    return detections


def detect_batch(
    frames: List[np.ndarray],
) -> tuple[List[List[YoloDetection]], float]:
    """Run YOLO on a batch of frames. Returns (per-frame detections, elapsed_ms)."""
    t0 = time.perf_counter()
    all_detections: List[List[YoloDetection]] = []
    for idx, frame in enumerate(frames):
        dets = detect_frame(frame, frame_index=idx)
        all_detections.append(dets)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "YOLO batch: %d frames, %d total detections, %.1f ms",
        len(frames),
        sum(len(d) for d in all_detections),
        elapsed_ms,
    )
    return all_detections, elapsed_ms
