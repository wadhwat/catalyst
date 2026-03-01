from fastapi.testclient import TestClient

import src.api.server as server


def test_inspect_persists_frames_and_serves_media(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "INSPECTIONS_DIR", tmp_path / "inspections")

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
    assert payload["evidence_frames"]
    assert payload["evidence_urls"]

    frame_name = payload["evidence_frames"][0]
    frame_path = tmp_path / "inspections" / payload["inspection_id"] / frame_name
    assert frame_path.exists()

    media_url = payload["evidence_urls"][0]
    media_response = client.get(media_url)
    assert media_response.status_code == 200
