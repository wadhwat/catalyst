"""
Talk to the GPU EC2 inference service. We send frames, it runs YOLO + Qwen,
and sends back defect mappings. Keeps the heavy lifting off the main app server.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import List

import cv2
import httpx
import numpy as np

from src.inspection.schema import FrameError, MappedDefect, VlmFrameResult, YoloDetection

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return os.getenv("INFERENCE_SERVICE_URL", "http://localhost:9000").rstrip("/")


def _get_timeout() -> float:
    try:
        return float(os.getenv("INFERENCE_TIMEOUT_SEC", "60"))
    except ValueError:
        return 60.0


def _get_concurrency() -> int:
    try:
        return int(os.getenv("INFERENCE_CONCURRENCY_LIMIT", "5"))
    except ValueError:
        return 5


async def call_inference_service(
    image: np.ndarray,
    frame_index: int,
    semaphore: asyncio.Semaphore,
) -> tuple[List[YoloDetection], VlmFrameResult]:
    """
    Send a single frame to the EC2 inference service.
    The semaphore keeps us from hammering the GPU with too many concurrent requests.
    """
    _, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    image_bytes = buf.tobytes()

    async with semaphore:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=_get_timeout()) as client:
                response = await client.post(
                    f"{_get_base_url()}/detect",
                    files={"file": (f"frame_{frame_index:03d}.jpg", image_bytes, "image/jpeg")},
                )

            elapsed = (time.perf_counter() - t0) * 1000
            logger.info("Inference service frame %d: %.0f ms (status %d)", frame_index, elapsed, response.status_code)

            if response.status_code != 200:
                error_msg = f"Inference service returned {response.status_code}: {response.text[:200]}"
                return [], VlmFrameResult(frame_index=frame_index, error=error_msg)

            data = response.json()

            detections = [
                YoloDetection(
                    detection_id=d["detection_id"],
                    class_name=d["class_name"],
                    confidence=d["confidence"],
                    bbox=d["bbox_norm"],
                    frame_index=frame_index,
                )
                for d in data.get("detections", [])
            ]

            mapped_defects = [
                MappedDefect(**d) for d in data.get("mapped_defects", [])
            ]

            error = data.get("error")
            return detections, VlmFrameResult(
                frame_index=frame_index,
                mapped_defects=mapped_defects,
                error=error,
            )

        except Exception as exc:
            # Don't let one bad frame kill the whole batch — return partial info
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error("Inference service frame %d failed after %.0f ms: %s", frame_index, elapsed, exc)
            return [], VlmFrameResult(frame_index=frame_index, error=str(exc))


async def process_frames(
    frames: List[np.ndarray],
) -> tuple[List[List[YoloDetection]], List[VlmFrameResult], float]:
    """
    Fan out to the EC2 service in parallel. Concurrency is capped so we don't
    overload the GPU or hit rate limits.
    """
    semaphore = asyncio.Semaphore(_get_concurrency())
    t0 = time.perf_counter()

    tasks = [
        call_inference_service(frame, idx, semaphore)
        for idx, frame in enumerate(frames)
    ]

    results = await asyncio.gather(*tasks)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    per_frame_detections: List[List[YoloDetection]] = []
    vlm_results: List[VlmFrameResult] = []

    for detections, vlm_result in results:
        per_frame_detections.append(detections)
        if vlm_result.mapped_defects or vlm_result.error:
            vlm_results.append(vlm_result)

    total_dets = sum(len(d) for d in per_frame_detections)
    total_defects = sum(len(r.mapped_defects) for r in vlm_results)
    errors = sum(1 for r in vlm_results if r.error)
    logger.info(
        "Inference batch: %d frames, %d detections, %d mapped defects, %d errors, %.0f ms",
        len(frames), total_dets, total_defects, errors, elapsed_ms,
    )

    return per_frame_detections, vlm_results, elapsed_ms
