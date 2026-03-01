from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.server import app

client = TestClient(app)


def _make_test_image() -> bytes:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[100:200, 100:200] = [0, 0, 255]
    import cv2
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _mock_yolo_result(img_h: int = 480, img_w: int = 640):
    """Build a mock YOLO result with one detection."""
    box = MagicMock()
    box.xyxy = [MagicMock()]
    box.xyxy[0].cpu.return_value.numpy.return_value = np.array(
        [100.0, 100.0, 200.0, 200.0]
    )
    box.cls = [MagicMock()]
    box.cls[0].item.return_value = 0
    box.conf = [MagicMock()]
    box.conf[0].item.return_value = 0.92

    result = MagicMock()
    result.boxes = [box]
    result.names = {0: "corrosion"}
    return [result]


VLM_RESPONSE = json.dumps(
    {
        "mapped_defects": [
            {
                "detection_id": 1,
                "checklist_item": "Boom, cylinders",
                "defect_type": "corrosion",
                "confirmed": True,
                "severity": "Moderate",
                "description": "Visible rust on the boom arm near pivot point.",
                "bbox": [0.2344, 0.3125, 0.1563, 0.2083],
            }
        ]
    }
)


@pytest.fixture
def mock_yolo():
    mock_model = MagicMock()
    mock_model.predict.return_value = _mock_yolo_result()
    with patch("src.inspection.yolo_detector._load_model", return_value=mock_model):
        with patch("src.inspection.yolo_detector._weights_name", "test_model.pt"):
            yield mock_model


@pytest.fixture
def mock_openai():
    choice = MagicMock()
    choice.message.content = VLM_RESPONSE

    completion = MagicMock()
    completion.choices = [choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=completion)

    with patch("src.inspection.vlm_client._get_client", return_value=mock_client):
        yield mock_client


class TestInferEndpoint:
    def test_requires_input(self):
        resp = client.post(
            "/inspect/infer",
            data={"inspection_id": "test-1"},
        )
        assert resp.status_code == 400

    def test_single_image_full_pipeline(self, mock_yolo, mock_openai):
        img_bytes = _make_test_image()
        resp = client.post(
            "/inspect/infer",
            data={"inspection_id": "test-full"},
            files=[("frames", ("test.jpg", io.BytesIO(img_bytes), "image/jpeg"))],
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["inspection_id"] == "test-full"
        assert "findings" in body
        assert "report" in body
        assert "processing_stats" in body
        assert body["processing_stats"]["frame_count"] == 1

        assert len(body["findings"]) >= 1
        f = body["findings"][0]
        assert f["checklist_item"] == "Boom, cylinders"
        assert f["defect_type"] == "corrosion"
        assert f["severity"] == "Moderate"

        report = body["report"]
        assert report["summary"]["status"] in ("PASS", "MONITOR", "FAIL")
        assert len(report["items"]) > 0

    def test_no_detections_returns_all_pass(self, mock_openai):
        mock_model = MagicMock()
        empty_result = MagicMock()
        empty_result.boxes = []
        mock_model.predict.return_value = [empty_result]

        with patch("src.inspection.yolo_detector._load_model", return_value=mock_model):
            with patch("src.inspection.yolo_detector._weights_name", "test.pt"):
                img_bytes = _make_test_image()
                resp = client.post(
                    "/inspect/infer",
                    data={"inspection_id": "test-clean"},
                    files=[("frames", ("test.jpg", io.BytesIO(img_bytes), "image/jpeg"))],
                )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["findings"]) == 0
        assert body["report"]["summary"]["status"] == "PASS"

    def test_multiple_frames(self, mock_yolo, mock_openai):
        img_bytes = _make_test_image()
        files = [
            ("frames", (f"frame_{i}.jpg", io.BytesIO(img_bytes), "image/jpeg"))
            for i in range(3)
        ]
        resp = client.post(
            "/inspect/infer",
            data={"inspection_id": "test-multi"},
            files=files,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["processing_stats"]["frame_count"] == 3
