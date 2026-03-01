from fastapi.testclient import TestClient

import src.api.server as server
from src.inspection.report_builder import build_report


def test_inspect_persists_frames_and_serves_media(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "INSPECTIONS_DIR", tmp_path / "inspections")
    monkeypatch.setattr(server, "detect_batch", lambda frames: ([], 0.0))

    async def mock_check_health():
        return True

    monkeypatch.setattr(server, "check_inference_health", mock_check_health)

    async def mock_classify(frames, detections):
        return [], 0.0

    async def mock_generate_report(findings, evidence_frames, parts=None):
        return build_report(findings, evidence_frames), 0.0

    async def mock_narrative(report, history):
        return ""

    monkeypatch.setattr(server, "classify_frames", mock_classify)
    monkeypatch.setattr(server, "aggregate_findings", lambda results, ts: ([], 0.0))
    monkeypatch.setattr(server, "generate_report_via_llm", mock_generate_report)
    monkeypatch.setattr(server, "build_narrative", mock_narrative)

    client = TestClient(server.app)

    response = client.post(
        "/inspect",
        data={
            "machine_type": "loader",
            "niche": "construction",
            "client_trace_id": "test-trace-123",
            "vin": "VIN123",
        },
        files={"file": ("sample.jpg", b"not-a-real-image", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["inspection_id"] == "test-trace-123"
    assert "report_pdf_url" in payload
    assert payload["evidence_frames"]
    assert payload["evidence_urls"]
    assert "findings" in payload
    assert "report" in payload

    frame_name = payload["evidence_frames"][0]
    frame_path = tmp_path / "inspections" / payload["inspection_id"] / frame_name
    assert frame_path.exists()

    media_url = payload["evidence_urls"][0]
    media_response = client.get(media_url)
    assert media_response.status_code == 200
