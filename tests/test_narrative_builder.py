import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.inspection.narrative_builder import build_narrative


def test_build_narrative_returns_text():
    response_payload = {"narrative": "Inspection shows recurring corrosion on the boom."}
    choice = MagicMock()
    choice.message.content = json.dumps(response_payload)
    completion = MagicMock()
    completion.choices = [choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=completion)

    with patch("src.inspection.narrative_builder._get_client", return_value=mock_client):
        narrative = asyncio.run(build_narrative({"summary": {"status": "FAIL"}, "items": []}, []))

    assert "corrosion" in narrative
