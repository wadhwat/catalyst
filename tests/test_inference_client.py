from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.inspection.inference_client import (
    call_inference_service,
    process_frames,
)


def _make_frame(h: int = 480, w: int = 640) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _mock_httpx_response(data: dict, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    resp.text = json.dumps(data)
    return resp


def _mock_async_client(response):
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=response)
    return mock_client


EC2_RESPONSE_OK = {
    "detections": [
        {
            "detection_id": 1,
            "class_name": "corrosion",
            "confidence": 0.88,
            "bbox_norm": [0.5, 0.4, 0.1, 0.08],
            "bbox_pixel": [288, 173, 352, 211],
        }
    ],
    "mapped_defects": [
        {
            "detection_id": 1,
            "checklist_item": "Radiator",
            "defect_type": "corrosion",
            "confirmed": True,
            "severity": "Minor",
            "description": "Light surface rust on radiator housing.",
            "bbox": [0.5, 0.4, 0.1, 0.08],
        }
    ],
    "qwen_raw": "{}",
    "error": None,
}

EC2_RESPONSE_EMPTY = {
    "detections": [],
    "mapped_defects": [],
    "qwen_raw": None,
    "error": None,
}

EC2_RESPONSE_QWEN_ERROR = {
    "detections": [
        {
            "detection_id": 1,
            "class_name": "corrosion",
            "confidence": 0.72,
            "bbox_norm": [0.3, 0.3, 0.1, 0.1],
            "bbox_pixel": [160, 112, 224, 160],
        }
    ],
    "mapped_defects": [],
    "qwen_raw": None,
    "error": "Qwen timeout after 30s",
}


class TestCallInferenceService:
    @pytest.mark.asyncio
    async def test_successful_call(self):
        mock_client = _mock_async_client(_mock_httpx_response(EC2_RESPONSE_OK))
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 0, semaphore)

        assert len(dets) == 1
        assert dets[0].class_name == "corrosion"
        assert dets[0].confidence == 0.88
        assert dets[0].frame_index == 0
        assert len(vlm_result.mapped_defects) == 1
        assert vlm_result.mapped_defects[0].checklist_item == "Radiator"
        assert vlm_result.error is None

    @pytest.mark.asyncio
    async def test_no_detections(self):
        mock_client = _mock_async_client(_mock_httpx_response(EC2_RESPONSE_EMPTY))
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 0, semaphore)

        assert dets == []
        assert vlm_result.mapped_defects == []
        assert vlm_result.error is None

    @pytest.mark.asyncio
    async def test_qwen_error_still_returns_detections(self):
        mock_client = _mock_async_client(_mock_httpx_response(EC2_RESPONSE_QWEN_ERROR))
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 0, semaphore)

        assert len(dets) == 1
        assert vlm_result.mapped_defects == []
        assert vlm_result.error == "Qwen timeout after 30s"

    @pytest.mark.asyncio
    async def test_http_500_returns_error(self):
        mock_client = _mock_async_client(
            _mock_httpx_response({"error": "GPU OOM"}, status_code=500)
        )
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 3, semaphore)

        assert dets == []
        assert vlm_result.frame_index == 3
        assert vlm_result.error is not None
        assert "500" in vlm_result.error

    @pytest.mark.asyncio
    async def test_network_exception_returns_error(self):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=ConnectionError("Connection refused"))
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 0, semaphore)

        assert dets == []
        assert "Connection refused" in vlm_result.error

    @pytest.mark.asyncio
    async def test_malformed_json_returns_error(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = json.JSONDecodeError("bad", "", 0)
        resp.text = "not json"
        mock_client = _mock_async_client(resp)
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 0, semaphore)

        assert dets == []
        assert vlm_result.error is not None

    @pytest.mark.asyncio
    async def test_frame_index_passed_through(self):
        mock_client = _mock_async_client(_mock_httpx_response(EC2_RESPONSE_OK))
        semaphore = asyncio.Semaphore(5)

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            dets, vlm_result = await call_inference_service(_make_frame(), 7, semaphore)

        assert all(d.frame_index == 7 for d in dets)
        assert vlm_result.frame_index == 7


class TestProcessFrames:
    @pytest.mark.asyncio
    async def test_empty_frames_list(self):
        all_dets, vlm_results, elapsed = await process_frames([])
        assert all_dets == []
        assert vlm_results == []
        assert elapsed >= 0

    @pytest.mark.asyncio
    async def test_multiple_frames_parallel(self):
        mock_client = _mock_async_client(_mock_httpx_response(EC2_RESPONSE_OK))

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            frames = [_make_frame() for _ in range(3)]
            all_dets, vlm_results, elapsed = await process_frames(frames)

        assert len(all_dets) == 3
        assert all(len(d) == 1 for d in all_dets)
        assert len(vlm_results) == 3

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(self):
        call_count = 0

        async def alternating_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                return _mock_httpx_response({"error": "fail"}, status_code=500)
            return _mock_httpx_response(EC2_RESPONSE_OK)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = alternating_post

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            frames = [_make_frame() for _ in range(4)]
            all_dets, vlm_results, elapsed = await process_frames(frames)

        assert len(all_dets) == 4
        successes = sum(1 for d in all_dets if len(d) > 0)
        failures = sum(1 for r in vlm_results if r.error)
        assert successes == 2
        assert failures == 2

    @pytest.mark.asyncio
    async def test_no_detection_frames_excluded_from_vlm_results(self):
        mock_client = _mock_async_client(_mock_httpx_response(EC2_RESPONSE_EMPTY))

        with patch("src.inspection.inference_client.httpx.AsyncClient", return_value=mock_client):
            frames = [_make_frame() for _ in range(2)]
            all_dets, vlm_results, elapsed = await process_frames(frames)

        assert len(all_dets) == 2
        assert vlm_results == []
