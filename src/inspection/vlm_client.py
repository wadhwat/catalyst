from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from typing import List

import cv2
import numpy as np
from openai import AsyncOpenAI

from src.inspection.prompts import (
    VLM_RESPONSE_SCHEMA,
    VLM_SYSTEM_PROMPT,
    build_vlm_user_message,
    format_detections_block,
)
from src.inspection.schema import MappedDefect, VlmFrameResult, YoloDetection

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


def _get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def _get_concurrency() -> int:
    try:
        return int(os.getenv("VLM_CONCURRENCY_LIMIT", "5"))
    except ValueError:
        return 5


def _encode_frame_b64(image: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


async def classify_frame(
    image: np.ndarray,
    detections: List[YoloDetection],
    frame_index: int,
    semaphore: asyncio.Semaphore,
) -> VlmFrameResult:
    """Send a single frame + its YOLO detections to the VLM and parse the response."""
    if not detections:
        return VlmFrameResult(frame_index=frame_index)

    det_dicts = [d.model_dump() for d in detections]
    det_text = format_detections_block(det_dicts)
    user_text = build_vlm_user_message(det_text)
    img_b64 = _encode_frame_b64(image)

    async with semaphore:
        t0 = time.perf_counter()
        try:
            client = _get_client()
            response = await client.chat.completions.create(
                model=_get_model(),
                messages=[
                    {"role": "system", "content": VLM_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                response_format=VLM_RESPONSE_SCHEMA,
                temperature=0.1,
                max_tokens=2048,
            )
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info(
                "VLM frame %d: %.0f ms", frame_index, elapsed
            )

            raw = response.choices[0].message.content
            if not raw:
                return VlmFrameResult(
                    frame_index=frame_index, error="Empty VLM response"
                )

            parsed = json.loads(raw)
            mapped = [MappedDefect(**d) for d in parsed.get("mapped_defects", [])]
            return VlmFrameResult(frame_index=frame_index, mapped_defects=mapped)

        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error(
                "VLM frame %d failed after %.0f ms: %s",
                frame_index,
                elapsed,
                exc,
            )
            return VlmFrameResult(
                frame_index=frame_index, error=str(exc)
            )


async def classify_frames(
    frames: List[np.ndarray],
    per_frame_detections: List[List[YoloDetection]],
) -> tuple[List[VlmFrameResult], float]:
    """Run VLM classification on all frames that have detections, in parallel."""
    semaphore = asyncio.Semaphore(_get_concurrency())
    t0 = time.perf_counter()

    tasks = []
    for idx, (frame, dets) in enumerate(zip(frames, per_frame_detections)):
        if dets:
            tasks.append(classify_frame(frame, dets, idx, semaphore))

    results = await asyncio.gather(*tasks) if tasks else []
    elapsed_ms = (time.perf_counter() - t0) * 1000

    frames_called = len(tasks)
    total_defects = sum(len(r.mapped_defects) for r in results)
    errors = sum(1 for r in results if r.error)
    logger.info(
        "VLM batch: %d frames called, %d defects mapped, %d errors, %.0f ms total",
        frames_called,
        total_defects,
        errors,
        elapsed_ms,
    )

    return list(results), elapsed_ms
