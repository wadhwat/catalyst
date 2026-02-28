from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from src.utils.images import normalize_image_to_frame, write_blank_frame
from src.utils.video import sample_video_frames

app = FastAPI(title='CATalyst Inspect API')


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


@app.post('/inspect')
async def inspect(
    machine_type: str = Form(...),
    niche: str = Form(...),
    client_trace_id: str = Form(...),
    file: UploadFile = File(...),
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

    stub_report = {
        'summary': {
            'status': 'UNKNOWN',
            'notes': 'Stub report (no scoring yet).',
        },
        'items': [
            {
                'id': 'radiator_debris',
                'status': 'UNKNOWN',
                'notes': 'Stub item.',
            },
            {
                'id': 'hose_leak',
                'status': 'UNKNOWN',
                'notes': 'Stub item.',
            },
        ],
    }

    return {
        'client_trace_id': client_trace_id,
        'received': {
            'machine_type': machine_type,
            'niche': niche,
            'filename': filename,
            'content_type': file.content_type,
            'saved_path': saved_path,
        },
        'evidence_frames': evidence_frames,
        'frame_warning': frame_warning,
        'report': stub_report,
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('src.api.server:app', host='0.0.0.0', port=8000, reload=False)

