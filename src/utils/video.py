from __future__ import annotations

import os
from typing import List

import cv2

from .images import resize_max, save_jpeg


def sample_video_frames(
    video_path: str,
    out_dir: str,
    fps: int = 1,
    max_frames: int = 12,
    max_side: int = 1024,
    quality: int = 90,
) -> List[str]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f'Unable to open video: {video_path}')

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if not source_fps or source_fps <= 0:
        source_fps = 30.0
    sample_every = max(int(round(source_fps / float(fps))), 1)

    names: List[str] = []
    index = 0
    saved = 0
    while saved < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if index % sample_every == 0:
            frame = resize_max(frame, max_side=max_side)
            name = f'frame_{saved + 1:03d}.jpg'
            out_path = os.path.join(out_dir, name)
            save_jpeg(frame, out_path, quality=quality)
            names.append(name)
            saved += 1
        index += 1

    cap.release()
    return names

