import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.inspection.llm_reviewer import review_report
from src.inspection.schema import Finding
from src.report.schema import Report, ReportItem, ReportSummary


def test_review_report_returns_reviewed():
    findings = [
        Finding(
            checklist_item="Boom, cylinders",
            defect_type="corrosion",
            severity="Critical",
            description="Rust streaks near pivot point.",
            bbox=[0.1, 0.1, 0.2, 0.2],
            confidence=0.9,
            frame_index=0,
            timestamp_sec=0.0,
            needs_human_review=False,
        )
    ]
    draft = Report(
        summary=ReportSummary(status="MONITOR", notes="Draft summary"),
        items=[
            ReportItem(
                id="Boom, cylinders",
                status="MONITOR",
                notes="Draft note",
                evidence=["/media/one.jpg"],
            )
        ],
    )

    response_payload = {
        "summary": {"status": "FAIL", "notes": "Critical corrosion detected."},
        "items": [
            {
                "id": "Boom, cylinders",
                "status": "FAIL",
                "notes": "Severe corrosion on boom cylinder.",
                "evidence": ["/media/one.jpg"],
                "score": 0.95,
            }
        ],
    }

    choice = MagicMock()
    choice.message.content = json.dumps(response_payload)
    completion = MagicMock()
    completion.choices = [choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=completion)

    with patch("src.inspection.llm_reviewer._get_client", return_value=mock_client):
        reviewed = asyncio.run(review_report(findings, draft, ["/media/one.jpg"]))

    assert reviewed.summary.status == "FAIL"
    assert reviewed.items[0].status == "FAIL"
