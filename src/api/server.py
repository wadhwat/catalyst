from __future__ import annotations

import hashlib

from dotenv import load_dotenv

load_dotenv()
import json
import logging
import os
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import cv2

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.auth import db
from src.auth.routes import get_current_user, router as auth_router
from src.inspection.aggregation import aggregate_findings, compute_iou
from src.inspection.inference_client import check_inference_health, process_frames
from src.inspection.narrative_builder import build_narrative
from src.inspection.parts import load_parts
from src.inspection.report_builder import build_report
from src.inspection.report_llm import generate_report_via_llm
from src.inspection.report_pdf import generate_report_pdf
from src.inspection.routes import router as inspection_router
from src.memory.schema import EngineerNote, ItemSummary, MemoryReference, SessionSummary
from src.memory.routes import router as memory_router
from src.memory.supermemory_client import SupermemoryClient
from src.machines.routes import router as machines_router
from src.preferences.routes import router as preferences_router
from src.reports.routes import router as reports_router
from src.api.tts_routes import router as tts_router
from src.utils.images import load_image, normalize_image_to_frame, resize_max, write_blank_frame
from src.utils.video import sample_video_frames

app = FastAPI(title='CATalyst Inspect API')
app.include_router(auth_router)
app.include_router(inspection_router)
app.include_router(memory_router)
app.include_router(machines_router)
app.include_router(reports_router)
app.include_router(preferences_router)
app.include_router(tts_router)
logger = logging.getLogger(__name__)
memory_client = SupermemoryClient()
INSPECTIONS_DIR = Path('data') / 'inspections'


def get_weights_name() -> str:
    # Remote inference service owns YOLO weights; keep label configurable.
    return os.getenv('YOLO_WEIGHTS_NAME', 'remote')


def detect_batch(frame_images):
    """
    Backward-compatible shim for older /inspect pipeline tests.
    We run full remote inference inside classify_frames().
    """
    return [[] for _ in frame_images], 0.0


async def classify_frames(frame_images, per_frame_detections):
    """
    Backward-compatible shim for older /inspect pipeline tests.
    Returns (vlm_results, elapsed_ms) and exposes detections on
    classify_frames._last_per_frame_detections.
    """
    detected, vlm_results, elapsed_ms = await process_frames(frame_images)
    classify_frames._last_per_frame_detections = detected
    return vlm_results, elapsed_ms


@app.get('/health')
def health() -> Dict[str, bool]:
    return {'ok': True}


@app.get('/media/inspections/{inspection_id}/{filename}')
def get_inspection_frame(inspection_id: str, filename: str) -> FileResponse:
    safe_id = _safe_dir(inspection_id)
    safe_name = _safe_filename(filename)
    path = INSPECTIONS_DIR / safe_id / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail='frame not found')
    return FileResponse(path)


def _safe_filename(name: str | None) -> str:
    if not name:
        return 'upload.bin'
    base = os.path.basename(name)
    if not base:
        return 'upload.bin'
    return base


def _safe_dir(name: str | None) -> str:
    if not name:
        return 'inspection'
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return cleaned or 'inspection'


def _inspection_dir(inspection_id: str) -> Path:
    safe_id = _safe_dir(inspection_id)
    return INSPECTIONS_DIR / safe_id


def _build_evidence_urls(inspection_id: str, frames: List[str]) -> List[str]:
    safe_id = _safe_dir(inspection_id)
    return [f'/media/inspections/{safe_id}/{_safe_filename(name)}' for name in frames]


def _is_video(filename: str, content_type: str | None) -> bool:
    if content_type and content_type.startswith('video/'):
        return True
    ext = os.path.splitext(filename.lower())[1]
    return ext in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}


def _is_image(filename: str, content_type: str | None) -> bool:
    if content_type and content_type.startswith('image/'):
        return True
    ext = os.path.splitext(filename.lower())[1]
    return ext in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}


def _sha256_file(path: str) -> str | None:
    try:
        digest = hashlib.sha256()
        with open(path, 'rb') as handle:
            for chunk in iter(lambda: handle.read(8192), b''):
                digest.update(chunk)
        return digest.hexdigest()
    except Exception as exc:
        logger.warning('Failed to hash %s: %s', path, exc)
        return None


def _memory_enabled() -> bool:
    return bool(memory_client.api_key and memory_client.base_url)


@app.post('/inspect')
async def inspect(
    machine_type: str = Form(...),
    niche: str = Form(...),
    client_trace_id: str = Form(...),
    vin: str = Form(...),
    engineer_notes: str | None = Form(None),
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    if file is None:
        raise HTTPException(status_code=400, detail='file is required')

    temp_dir = tempfile.mkdtemp(prefix='catalyst_')
    filename = _safe_filename(file.filename)
    saved_path = os.path.join(temp_dir, filename)
    try:
        try:
            with open(saved_path, 'wb') as out:
                shutil.copyfileobj(file.file, out)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f'failed to save upload: {exc}')

        if not await check_inference_health():
            raise HTTPException(
                status_code=503,
                detail=(
                    'EC2 inference service is unreachable. Check INFERENCE_SERVICE_URL '
                    'and ensure the GPU server is running.'
                ),
            )

        t_total_start = time.perf_counter()
        fps_sample_rate = int(os.getenv('INSPECT_FPS_SAMPLE_RATE', '1'))
        max_frames = int(os.getenv('INSPECT_MAX_FRAMES', '12'))

        evidence_frames: List[str] = []
        frame_warning = None
        video_fps: float | None = None
        try:
            if _is_video(filename, file.content_type):
                cap = cv2.VideoCapture(saved_path)
                video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                cap.release()
                evidence_frames = sample_video_frames(
                    saved_path,
                    temp_dir,
                    fps=fps_sample_rate,
                    max_frames=max_frames,
                )
            elif _is_image(filename, file.content_type):
                evidence_frames = [normalize_image_to_frame(saved_path, temp_dir)]
            else:
                frame_warning = 'unknown file type; generated blank frame'
                evidence_frames = [write_blank_frame(temp_dir)]
        except Exception as exc:
            frame_warning = f'frame extraction failed; generated blank frame ({exc})'
            evidence_frames = [write_blank_frame(temp_dir)]

        inspection_id = _safe_dir(client_trace_id)
        inspection_dir = _inspection_dir(inspection_id)
        inspection_dir.mkdir(parents=True, exist_ok=True)

        persisted_frames: List[str] = []
        for frame_name in evidence_frames:
            safe_name = _safe_filename(frame_name)
            src = os.path.join(temp_dir, frame_name)
            dst = inspection_dir / safe_name
            if os.path.exists(src):
                shutil.copy2(src, dst)
                persisted_frames.append(safe_name)

        evidence_urls = _build_evidence_urls(inspection_id, persisted_frames)

        frame_images = []
        for frame_name in evidence_frames:
            path = os.path.join(temp_dir, frame_name)
            if not os.path.exists(path):
                path = str(inspection_dir / frame_name)
            try:
                img = load_image(path)
                frame_images.append(resize_max(img, max_side=1024))
            except Exception as exc:
                logger.warning('Failed to load frame %s: %s', frame_name, exc)

        if not frame_images:
            fallback = write_blank_frame(temp_dir)
            try:
                img = load_image(os.path.join(temp_dir, fallback))
                frame_images.append(resize_max(img, max_side=1024))
                evidence_frames = [fallback]
                persisted_frames = [fallback]
                evidence_urls = _build_evidence_urls(inspection_id, persisted_frames)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f'failed to build fallback frame: {exc}')

        per_frame_detections, yolo_ms = detect_batch(frame_images)
        vlm_results, vlm_ms = await classify_frames(frame_images, per_frame_detections)
        inferred_detections = getattr(classify_frames, '_last_per_frame_detections', None)
        if inferred_detections is not None:
            per_frame_detections = inferred_detections
        frames_with_dets = sum(1 for dets in per_frame_detections if dets)

        frame_timestamps: dict[int, float] | None = None
        if video_fps and fps_sample_rate > 0:
            frame_timestamps = {i: i / fps_sample_rate for i in range(len(frame_images))}

        findings, agg_ms = aggregate_findings(vlm_results, frame_timestamps)

        for finding in findings:
            if finding.confidence < 1e-9:
                for dets in per_frame_detections:
                    for det in dets:
                        if det.frame_index == finding.frame_index:
                            if compute_iou(det.bbox, finding.bbox) > 0.3:
                                finding.confidence = max(finding.confidence, det.confidence)

        parts = load_parts()
        try:
            report_obj, _ = await generate_report_via_llm(findings, evidence_urls, parts=parts)
            report_payload = report_obj.model_dump()
        except Exception as exc:
            logger.warning('GPT-4 report failed, using fallback: %s', exc)
            report_obj = build_report(findings, evidence_urls)
            report_payload = report_obj.model_dump()
        for item in report_payload.get('items', []):
            if not item.get('evidence'):
                item['evidence'] = list(evidence_urls)

        memory_context: List[Dict[str, Any]] = []
        memory_write_status: Dict[str, str] = {
            'session_summary': 'skipped',
            'engineer_note': 'skipped',
            'inspection_report': 'skipped',
            'vlm_findings': 'skipped',
            'inspection_narrative': 'skipped',
        }

        memory_tags = [f'vin:{vin}']
        if user:
            memory_tags.append(f'user:{user.id}')

        history_reports: List[Dict[str, Any]] = []
        if _memory_enabled():
            memory_context = memory_client.search_memories(tags=memory_tags, limit=5)
            history_results = memory_client.search_memories(
                tags=[*memory_tags, 'kind:inspection_report'],
                limit=5,
            )
            for item in history_results:
                content = item.get('content') if isinstance(item, dict) else None
                if isinstance(content, dict):
                    history_reports.append(content)
        else:
            logger.warning('Supermemory disabled (missing SUPERMEMORY_API_KEY or SUPERMEMORY_BASE_URL)')
            memory_write_status['session_summary'] = 'skipped_missing_config'
            memory_write_status['engineer_note'] = 'skipped_missing_config'
            memory_write_status['inspection_report'] = 'skipped_missing_config'
            memory_write_status['vlm_findings'] = 'skipped_missing_config'
            memory_write_status['inspection_narrative'] = 'skipped_missing_config'

        references: List[MemoryReference] = []
        saved_hash = _sha256_file(saved_path)
        if saved_hash:
            references.append(MemoryReference(filename=filename, sha256=saved_hash))
        for frame_name in persisted_frames:
            frame_path = inspection_dir / frame_name
            frame_hash = _sha256_file(str(frame_path))
            if frame_hash:
                references.append(MemoryReference(filename=frame_name, sha256=frame_hash))

        observed_at = datetime.now(timezone.utc).isoformat()
        inspection_items = []
        for item in report_payload.get('items', []):
            inspection_items.append(
                {
                    'id': item.get('id'),
                    'status': item.get('status'),
                    'notes': item.get('notes'),
                    'evidence_urls': item.get('evidence') or list(evidence_urls),
                    'recommended_parts': item.get('recommended_parts') or [],
                }
            )
        inspection_report = {
            'vin': vin,
            'client_trace_id': client_trace_id,
            'observed_at': observed_at,
            'summary': report_payload.get('summary'),
            'items': inspection_items,
        }

        narrative_text = None
        if _memory_enabled():
            narrative_text = await build_narrative(inspection_report, history_reports)
            if narrative_text:
                inspection_report['narrative'] = narrative_text

        report_pdf_url = None
        try:
            pdf_path = inspection_dir / 'report.pdf'
            if generate_report_pdf(
                report_obj,
                inspection_id=inspection_id,
                vin=vin,
                observed_at=observed_at,
                output_path=pdf_path,
            ):
                report_pdf_url = f'/media/inspections/{inspection_id}/report.pdf'
        except Exception as exc:
            logger.warning('PDF generation failed: %s', exc)

        if _memory_enabled():
            items = [
                ItemSummary(id=item['id'], status=item['status'], notes=item.get('notes'))
                for item in inspection_items
            ]
            session_summary = SessionSummary(
                vin=vin,
                client_trace_id=client_trace_id,
                summary_status=report_payload.get('summary', {}).get('status', 'UNKNOWN'),
                items=items,
                references=references,
            )
            created = memory_client.create_memory(
                kind='session_summary',
                content=session_summary.model_dump(mode='json'),
                tags=[*memory_tags, 'kind:session_summary'],
                metadata={'vin': vin, 'client_trace_id': client_trace_id},
            )
            memory_write_status['session_summary'] = 'ok' if created else 'error'

            if engineer_notes and engineer_notes.strip():
                note = EngineerNote(vin=vin, note=engineer_notes.strip())
                created_note = memory_client.create_memory(
                    kind='engineer_note',
                    content=note.model_dump(mode='json'),
                    tags=[*memory_tags, 'kind:engineer_note'],
                    metadata={'vin': vin, 'client_trace_id': client_trace_id},
                )
                memory_write_status['engineer_note'] = 'ok' if created_note else 'error'

            created_report = memory_client.create_memory(
                kind='inspection_report',
                content=inspection_report,
                tags=[*memory_tags, f'inspection:{client_trace_id}', 'kind:inspection_report'],
                metadata={'vin': vin, 'client_trace_id': client_trace_id, 'observed_at': observed_at},
            )
            memory_write_status['inspection_report'] = 'ok' if created_report else 'error'

            findings_payload = [finding.model_dump() for finding in findings]
            errors_payload = [
                {'frame_index': result.frame_index, 'stage': 'vlm', 'message': result.error}
                for result in vlm_results
                if result.error
            ]
            processing_stats = {
                'frame_count': len(frame_images),
                'frames_with_detections': frames_with_dets,
                'yolo_ms': round(yolo_ms, 1),
                'vlm_ms': round(vlm_ms, 1),
                'aggregation_ms': round(agg_ms, 1),
                'total_ms': round((time.perf_counter() - t_total_start) * 1000, 1),
            }
            vlm_content = {
                'inspection_id': client_trace_id,
                'vin': vin,
                'findings': findings_payload,
                'model_versions': {
                    'yolo_weights': get_weights_name(),
                    'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4o'),
                },
                'processing_stats': processing_stats,
                'errors': errors_payload,
            }
            created_findings = memory_client.create_memory(
                kind='vlm_findings',
                content=vlm_content,
                tags=[*memory_tags, f'inspection:{client_trace_id}', 'kind:vlm_findings'],
                metadata={'vin': vin, 'client_trace_id': client_trace_id, 'observed_at': observed_at},
            )
            memory_write_status['vlm_findings'] = 'ok' if created_findings else 'error'

            if narrative_text:
                created_narrative = memory_client.create_memory(
                    kind='inspection_narrative',
                    content={
                        'vin': vin,
                        'client_trace_id': client_trace_id,
                        'observed_at': observed_at,
                        'narrative': narrative_text,
                    },
                    tags=[*memory_tags, f'inspection:{client_trace_id}', 'kind:inspection_narrative'],
                    metadata={'vin': vin, 'client_trace_id': client_trace_id, 'observed_at': observed_at},
                )
                memory_write_status['inspection_narrative'] = (
                    'ok' if created_narrative else 'error'
                )

        if user:
            try:
                observed_at_db = datetime.now(timezone.utc).isoformat()
                report_json = json.dumps(inspection_report)
                items_json = json.dumps(inspection_report.get('items', []))
                evidence_json = json.dumps(evidence_urls)
                db.create_inspection_report(
                    user_id=user.id,
                    report_id=client_trace_id,
                    vin=vin,
                    observed_at=inspection_report.get('observed_at') or observed_at_db,
                    summary_status=report_payload.get('summary', {}).get('status', 'UNKNOWN'),
                    items_json=items_json,
                    evidence_urls_json=evidence_json,
                    report_json=report_json,
                    narrative_text=narrative_text,
                    created_at=observed_at_db,
                )
            except Exception as exc:
                logger.warning('Failed to persist inspection report to DB: %s', exc)

        findings_payload = [finding.model_dump() for finding in findings]

        return {
            'inspection_id': inspection_id,
            'client_trace_id': client_trace_id,
            'report_pdf_url': report_pdf_url,
            'received': {
                'machine_type': machine_type,
                'niche': niche,
                'vin': vin,
                'filename': filename,
                'content_type': file.content_type,
                'saved_path': saved_path,
            },
            'evidence_frames': persisted_frames,
            'evidence_urls': evidence_urls,
            'frame_warning': frame_warning,
            'findings': findings_payload,
            'report': report_payload,
            'narrative': narrative_text,
            'memory_context': memory_context,
            'memory_write_status': memory_write_status,
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('src.api.server:app', host='0.0.0.0', port=8000, reload=False)

