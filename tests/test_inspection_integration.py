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


EC2_RESPONSE_WITH_DETECTIONS = {
    "detections": [
        {
            "detection_id": 1,
            "class_name": "corrosion",
            "confidence": 0.92,
            "bbox_norm": [0.2344, 0.3125, 0.1563, 0.2083],
            "bbox_pixel": [100, 100, 200, 200],
        }
    ],
    "mapped_defects": [
        {
            "detection_id": 1,
            "checklist_item": "Boom, cylinders",
            "defect_type": "corrosion",
            "confirmed": True,
            "severity": "MODERATE",
            "description": "Visible rust on the boom arm near pivot point.",
            "bbox": [0.2344, 0.3125, 0.1563, 0.2083],
        }
    ],
    "qwen_raw": "{}",
    "error": None,
}

EC2_RESPONSE_NO_DETECTIONS = {
    "detections": [],
    "mapped_defects": [],
    "qwen_raw": None,
    "error": None,
}

GPT4_REPORT_RESPONSE = json.dumps({
    "summary": {"status": "MONITOR", "notes": "1 finding across 1 component."},
    "items": [
        {"id": "Boom, cylinders", "status": "MONITOR", "score": 0.92, "notes": "Corrosion detected on boom arm."},
        {"id": "Bucket/GET", "status": "PASS", "score": 0.0, "notes": "No defects detected."},
    ],
})


def _mock_ec2_response(response_data: dict, status_code: int = 200):
    """Create a mock httpx response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = response_data
    mock_resp.text = json.dumps(response_data)
    return mock_resp


@pytest.fixture
def mock_ec2_with_detections():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        return_value=_mock_ec2_response(EC2_RESPONSE_WITH_DETECTIONS)
    )
    with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_ec2_no_detections():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        return_value=_mock_ec2_response(EC2_RESPONSE_NO_DETECTIONS)
    )
    with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_gpt4():
    choice = MagicMock()
    choice.message.content = GPT4_REPORT_RESPONSE

    completion = MagicMock()
    completion.choices = [choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=completion)

    with patch("src.inspection.report_llm._get_client", return_value=mock_client):
        yield mock_client


class TestInferEndpoint:
    def test_requires_input(self):
        resp = client.post(
            "/inspect/infer",
            data={"inspection_id": "test-1"},
        )
        assert resp.status_code == 400

    def test_single_image_full_pipeline(self, mock_ec2_with_detections, mock_gpt4):
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
        assert f["severity"] == "MODERATE"

        report = body["report"]
        assert report["summary"]["status"] in ("PASS", "MONITOR", "FAIL")

    def test_no_detections_returns_pass(self, mock_ec2_no_detections, mock_gpt4):
        img_bytes = _make_test_image()
        resp = client.post(
            "/inspect/infer",
            data={"inspection_id": "test-clean"},
            files=[("frames", ("test.jpg", io.BytesIO(img_bytes), "image/jpeg"))],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["findings"]) == 0

    def test_multiple_frames(self, mock_ec2_with_detections, mock_gpt4):
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

    def test_ec2_failure_returns_partial(self, mock_gpt4):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            return_value=_mock_ec2_response({"error": "GPU OOM"}, status_code=500)
        )
        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            img_bytes = _make_test_image()
            resp = client.post(
                "/inspect/infer",
                data={"inspection_id": "test-error"},
                files=[("frames", ("test.jpg", io.BytesIO(img_bytes), "image/jpeg"))],
            )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["errors"]) >= 1
        assert body["findings"] == []
