from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.inspection.report_llm import (
    _findings_to_text,
    generate_report_via_llm,
)
from src.inspection.schema import Finding


def _make_finding(
    checklist_item: str = "Boom, cylinders",
    defect_type: str = "corrosion",
    severity: str = "Moderate",
    confidence: float = 0.85,
    frame_index: int = 0,
) -> Finding:
    return Finding(
        checklist_item=checklist_item,
        defect_type=defect_type,
        severity=severity,
        description=f"Test {defect_type} on {checklist_item}",
        bbox=[0.5, 0.5, 0.1, 0.1],
        confidence=confidence,
        frame_index=frame_index,
    )


GPT4_REPORT = {
    "summary": {"status": "MONITOR", "notes": "1 finding on Boom, cylinders."},
    "items": [
        {
            "id": "Boom, cylinders",
            "status": "MONITOR",
            "score": 0.85,
            "notes": "Corrosion detected.",
        },
        {
            "id": "Bucket/GET",
            "status": "PASS",
            "score": 0.0,
            "notes": "No defects detected.",
        },
    ],
}

GPT4_REPORT_ALL_PASS = {
    "summary": {"status": "PASS", "notes": "No defects detected."},
    "items": [
        {
            "id": "Bucket/GET",
            "status": "PASS",
            "score": 0.0,
            "notes": "No defects detected.",
        },
    ],
}


def _mock_gpt4_client(response_data: dict):
    choice = MagicMock()
    choice.message.content = json.dumps(response_data)
    completion = MagicMock()
    completion.choices = [choice]
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=completion)
    return mock_client


class TestFindingsToText:
    def test_empty_findings(self):
        result = _findings_to_text([])
        assert "No defect findings" in result
        assert "PASS" in result

    def test_single_finding(self):
        f = _make_finding()
        result = _findings_to_text([f])
        assert "Boom, cylinders" in result
        assert "corrosion" in result
        assert "Moderate" in result
        assert "0.85" in result

    def test_multiple_findings_numbered(self):
        findings = [
            _make_finding(checklist_item="Boom, cylinders"),
            _make_finding(checklist_item="Radiator", severity="Critical"),
        ]
        result = _findings_to_text(findings)
        assert result.startswith("1.")
        assert "2." in result
        assert "Critical" in result


class TestGenerateReportViaLlm:
    @pytest.mark.asyncio
    async def test_successful_report(self):
        mock_client = _mock_gpt4_client(GPT4_REPORT)
        with patch("src.inspection.report_llm._get_client", return_value=mock_client):
            findings = [_make_finding()]
            report, elapsed = await generate_report_via_llm(findings, ["frame_001.jpg"])

        assert report.summary.status == "MONITOR"
        assert len(report.items) == 2
        assert report.items[0].id == "Boom, cylinders"
        assert report.items[0].evidence == ["frame_001.jpg"]
        assert elapsed > 0

    @pytest.mark.asyncio
    async def test_all_pass_report(self):
        mock_client = _mock_gpt4_client(GPT4_REPORT_ALL_PASS)
        with patch("src.inspection.report_llm._get_client", return_value=mock_client):
            report, elapsed = await generate_report_via_llm([], ["frame_001.jpg"])

        assert report.summary.status == "PASS"

    @pytest.mark.asyncio
    async def test_empty_response_raises(self):
        choice = MagicMock()
        choice.message.content = ""
        completion = MagicMock()
        completion.choices = [choice]
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=completion)

        with patch("src.inspection.report_llm._get_client", return_value=mock_client):
            with pytest.raises(ValueError, match="Empty GPT-4 response"):
                await generate_report_via_llm([], [])

    @pytest.mark.asyncio
    async def test_api_error_raises(self):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("Rate limit exceeded")
        )
        with patch("src.inspection.report_llm._get_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Rate limit"):
                await generate_report_via_llm([_make_finding()], [])

    @pytest.mark.asyncio
    async def test_evidence_frames_attached_to_items(self):
        mock_client = _mock_gpt4_client(GPT4_REPORT)
        frames = ["frame_001.jpg", "frame_002.jpg"]
        with patch("src.inspection.report_llm._get_client", return_value=mock_client):
            report, _ = await generate_report_via_llm([_make_finding()], frames)

        for item in report.items:
            assert item.evidence == frames

    @pytest.mark.asyncio
    async def test_recommended_parts_when_provided_by_gpt(self):
        report_with_parts = {
            "summary": {"status": "MONITOR", "notes": "1 finding."},
            "items": [
                {
                    "id": "Boom, cylinders",
                    "status": "MONITOR",
                    "score": 0.85,
                    "notes": "Corrosion detected.",
                    "recommended_parts": ["492-110", "3K-7380"],
                },
                {"id": "Bucket/GET", "status": "PASS", "score": 0.0, "notes": "No defects."},
            ],
        }
        mock_client = _mock_gpt4_client(report_with_parts)
        with patch("src.inspection.report_llm._get_client", return_value=mock_client):
            report, _ = await generate_report_via_llm(
                [_make_finding()], ["frame_001.jpg"], parts=[{"part_number": "492-110", "name": "Boom Pin"}]
            )
        boom = next(i for i in report.items if i.id == "Boom, cylinders")
        assert boom.recommended_parts == ["492-110", "3K-7380"]
        bucket = next(i for i in report.items if i.id == "Bucket/GET")
        assert bucket.recommended_parts == []
