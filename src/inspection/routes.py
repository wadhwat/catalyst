from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time
from typing import List, Optional

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.auth.routes import get_current_user
from src.inspection.aggregation import aggregate_findings
from src.inspection.report_builder import build_report
from src.inspection.schema import (
    FrameError,
    InferenceResponse,
    ModelVersions,
    ProcessingStats,
)
from src.inspection.vlm_client import classify_frames
from src.inspection.yolo_detector import detect_batch, get_weights_name
from src.utils.images import load_image, resize_max
from src.utils.video import sample_video_frames

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inspect", tags=["inspection"])


def _is_video(filename: str, content_type: str | None) -> bool:
    if content_type and content_type.startswith("video/"):
        return True
    ext = os.path.splitext(filename.lower())[1]
    return ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}


@router.post("/infer", response_model=InferenceResponse)
async def infer(
    video: Optional[UploadFile] = File(None),
    frames: List[UploadFile] = File(default=[]),
    inspection_id: str = Form(...),
    machine_model: Optional[str] = Form(None),
    checklist_version: Optional[str] = Form(None),
    fps_sample_rate: int = Form(2),
    max_frames: int = Form(20),
    user=Depends(get_current_user),
) -> InferenceResponse:
    t_total_start = time.perf_counter()
    errors: List[FrameError] = []
    temp_dir = tempfile.mkdtemp(prefix="catalyst_infer_")

    try:
        # --- 1. Frame extraction ---
        t_extract = time.perf_counter()
        frame_images = []
        frame_names: List[str] = []
        video_fps: float | None = None

        if video and video.filename:
            saved_path = os.path.join(temp_dir, os.path.basename(video.filename))
            with open(saved_path, "wb") as out:
                shutil.copyfileobj(video.file, out)

            if not _is_video(video.filename, video.content_type):
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded file does not appear to be a video: {video.filename}",
                )

            cap = cv2.VideoCapture(saved_path)
            video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.release()

            frame_names = sample_video_frames(
                saved_path, temp_dir, fps=fps_sample_rate, max_frames=max_frames
            )
            for name in frame_names:
                img = load_image(os.path.join(temp_dir, name))
                frame_images.append(resize_max(img, max_side=1024))

        elif frames:
            for i, upload in enumerate(frames[:max_frames]):
                try:
                    frame_path = os.path.join(
                        temp_dir, f"upload_{i:03d}.jpg"
                    )
                    with open(frame_path, "wb") as out:
                        shutil.copyfileobj(upload.file, out)
                    img = load_image(frame_path)
                    frame_images.append(resize_max(img, max_side=1024))
                    frame_names.append(f"upload_{i:03d}.jpg")
                except Exception as exc:
                    errors.append(
                        FrameError(
                            frame_index=i,
                            stage="extraction",
                            message=str(exc),
                        )
                    )
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either a 'video' upload or 'frames' image uploads.",
            )

        if not frame_images:
            raise HTTPException(
                status_code=400,
                detail="No valid frames could be extracted from the input.",
            )

        extract_ms = (time.perf_counter() - t_extract) * 1000
        logger.info(
            "Frame extraction: %d frames in %.0f ms",
            len(frame_images),
            extract_ms,
        )

        # --- 2. YOLO detection ---
        per_frame_detections, yolo_ms = detect_batch(frame_images)
        frames_with_dets = sum(1 for d in per_frame_detections if d)

        # --- 3. VLM classification (only frames with detections) ---
        vlm_results, vlm_ms = await classify_frames(
            frame_images, per_frame_detections
        )

        for result in vlm_results:
            if result.error:
                errors.append(
                    FrameError(
                        frame_index=result.frame_index,
                        stage="vlm",
                        message=result.error,
                    )
                )

        # --- 4. Aggregate / dedup ---
        frame_timestamps: dict[int, float] | None = None
        if video_fps and video_fps > 0:
            frame_timestamps = {
                i: i / fps_sample_rate for i in range(len(frame_images))
            }

        findings, agg_ms = aggregate_findings(vlm_results, frame_timestamps)

        # Backfill YOLO confidence onto findings
        yolo_conf_map: dict[tuple[int, int], float] = {}
        for dets in per_frame_detections:
            for det in dets:
                yolo_conf_map[(det.frame_index, det.detection_id)] = det.confidence

        for f in findings:
            if f.confidence < 1e-9:
                for dets in per_frame_detections:
                    for det in dets:
                        if det.frame_index == f.frame_index:
                            from src.inspection.aggregation import compute_iou
                            if compute_iou(det.bbox, f.bbox) > 0.3:
                                f.confidence = max(f.confidence, det.confidence)

        # --- 5. Build report ---
        report = build_report(findings, frame_names)

        total_ms = (time.perf_counter() - t_total_start) * 1000
        logger.info(
            "Inspection %s complete: %d findings, %.0f ms total",
            inspection_id,
            len(findings),
            total_ms,
        )

        return InferenceResponse(
            inspection_id=inspection_id,
            model_versions=ModelVersions(
                yolo_weights=get_weights_name(),
                openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            ),
            findings=findings,
            report=report,
            processing_stats=ProcessingStats(
                frame_count=len(frame_images),
                frames_with_detections=frames_with_dets,
                yolo_ms=round(yolo_ms, 1),
                vlm_ms=round(vlm_ms, 1),
                aggregation_ms=round(agg_ms, 1),
                total_ms=round(total_ms, 1),
            ),
            errors=errors,
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
