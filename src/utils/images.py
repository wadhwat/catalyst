from __future__ import annotations

import os
from typing import Tuple

import cv2
import numpy as np


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f'Unable to read image: {path}')
    return img


def resize_max(img: np.ndarray, max_side: int = 1024) -> np.ndarray:
    height, width = img.shape[:2]
    max_dim = max(height, width)
    if max_dim <= max_side:
        return img
    scale = max_side / float(max_dim)
    new_w = max(1, int(round(width * scale)))
    new_h = max(1, int(round(height * scale)))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def save_jpeg(img: np.ndarray, path: str, quality: int = 90) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


def normalize_image_to_frame(
    image_path: str,
    out_dir: str,
    frame_index: int = 1,
    max_side: int = 1024,
    quality: int = 90,
) -> str:
    img = load_image(image_path)
    img = resize_max(img, max_side=max_side)
    name = f'frame_{frame_index:03d}.jpg'
    out_path = os.path.join(out_dir, name)
    save_jpeg(img, out_path, quality=quality)
    return name


def write_blank_frame(
    out_dir: str,
    frame_index: int = 1,
    size: Tuple[int, int] = (640, 480),
    quality: int = 90,
) -> str:
    width, height = size
    img = np.zeros((height, width, 3), dtype=np.uint8)
    name = f'frame_{frame_index:03d}.jpg'
    out_path = os.path.join(out_dir, name)
    save_jpeg(img, out_path, quality=quality)
    return name

