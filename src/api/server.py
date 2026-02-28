from __future__ import annotations

import hashlib
import logging
import os
import shutil
import tempfile
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from src.auth.routes import get_current_user, router as auth_router
from src.corrections.routes import router as corrections_router
from src.memory.routes import router as memory_router
from src.memory.schema import EngineerNote, ItemSummary, MemoryReference, SessionSummary
from src.memory.supermemory_client import SupermemoryClient
from src.report.generate_baseline import generate_baseline
from src.utils.images import normalize_image_to_frame, write_blank_frame
from src.utils.video import sample_video_frames
from src.vlm.classifier import EquipmentClassifier

app = FastAPI(title='CATalyst Inspect API')
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(corrections_router)
logger = logging.getLogger(__name__)
memory_client = SupermemoryClient()
equipment_classifier = EquipmentClassifier()


@app.get('/health')
def health() -> Dict[str, bool]:
    return {'ok': True}


def _safe_filename(name: str | None) -> str:
    if not name:
        return 'upload.bin'
    base = os.path.basename(name)
    if not base:
        return 'upload.bin'
    return base


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
        with open(saved_path, 'wb') as out:
            shutil.copyfileobj(file.file, out)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'failed to save upload: {exc}')

    evidence_frames: List[str] = []
    frame_warning = None
    try:
        if _is_video(filename, file.content_type):
            evidence_frames = sample_video_frames(saved_path, temp_dir, fps=1, max_frames=12)
        elif _is_image(filename, file.content_type):
            evidence_frames = [normalize_image_to_frame(saved_path, temp_dir)]
        else:
            frame_warning = 'unknown file type; generated blank frame'
            evidence_frames = [write_blank_frame(temp_dir)]
    except Exception as exc:
        frame_warning = f'frame extraction failed; generated blank frame ({exc})'
        evidence_frames = [write_blank_frame(temp_dir)]

    # Classify using VLM (or fallback to empty scores if VLM unavailable)
    vlm_results: Dict[str, Any] = {}
    try:
        frame_paths = [os.path.join(temp_dir, f) for f in evidence_frames]
        vlm_results = equipment_classifier.classify_all_items(
            frame_paths=frame_paths,
            vin=vin,
            user_id=user.id if user else None,
        )
        scores = {item_id: result.score for item_id, result in vlm_results.items()}
    except Exception as exc:
        logger.warning('VLM classification failed, using fallback: %s', exc)
        scores = {}

    baseline_report = generate_baseline(scores, evidence_frames)

    # Persist frames for correction retrieval
    frame_storage_dir = os.getenv('FRAME_STORAGE_DIR', '/tmp/catalyst_frames')
    os.makedirs(frame_storage_dir, exist_ok=True)
    for frame_name in evidence_frames:
        frame_path = os.path.join(temp_dir, frame_name)
        frame_hash = _sha256_file(frame_path)
        if frame_hash:
            dest_path = os.path.join(frame_storage_dir, f'{frame_hash}.jpg')
            if not os.path.exists(dest_path):
                try:
                    shutil.copy2(frame_path, dest_path)
                except Exception as copy_exc:
                    logger.warning('Failed to persist frame %s: %s', frame_name, copy_exc)
    report_payload = baseline_report.model_dump()

    memory_context: List[Dict[str, Any]] = []
    memory_write_status: Dict[str, str] = {
        'session_summary': 'skipped',
        'engineer_note': 'skipped',
    }

    memory_tags = [f'vin:{vin}']
    if user:
        memory_tags.append(f'user:{user.id}')

    if _memory_enabled():
        memory_context = memory_client.search_memories(tags=memory_tags, limit=5)
    else:
        logger.warning('Supermemory disabled (missing SUPERMEMORY_API_KEY or SUPERMEMORY_BASE_URL)')
        memory_write_status['session_summary'] = 'skipped_missing_config'
        memory_write_status['engineer_note'] = 'skipped_missing_config'

    references: List[MemoryReference] = []
    saved_hash = _sha256_file(saved_path)
    if saved_hash:
        references.append(MemoryReference(filename=filename, sha256=saved_hash))
    for frame_name in evidence_frames:
        frame_path = os.path.join(temp_dir, frame_name)
        frame_hash = _sha256_file(frame_path)
        if frame_hash:
            references.append(MemoryReference(filename=frame_name, sha256=frame_hash))

    if _memory_enabled():
        items = [
            ItemSummary(id=item.id, status=item.status, notes=item.notes)
            for item in baseline_report.items
        ]
        session_summary = SessionSummary(
            vin=vin,
            client_trace_id=client_trace_id,
            summary_status=baseline_report.summary.status,
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

    # Build VLM classifications for frontend
    vlm_classifications = {}
    for item_id, result in vlm_results.items():
        vlm_classifications[item_id] = {
            'status': result.status,
            'score': result.score,
            'confidence': result.confidence,
            'reasoning': result.reasoning,
        }

    return {
        'client_trace_id': client_trace_id,
        'received': {
            'machine_type': machine_type,
            'niche': niche,
            'vin': vin,
            'filename': filename,
            'content_type': file.content_type,
            'saved_path': saved_path,
        },
        'evidence_frames': evidence_frames,
        'frame_warning': frame_warning,
        'report': report_payload,
        'vlm_classifications': vlm_classifications,
        'memory_context': memory_context,
        'memory_write_status': memory_write_status,
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('src.api.server:app', host='0.0.0.0', port=8000, reload=False)

