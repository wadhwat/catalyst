from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.vlm.classifier import EquipmentClassifier
from src.vlm.prompts import SYSTEM_PROMPT, build_item_prompt
from src.vlm.schema import ClassificationResult


def test_classification_result_model() -> None:
    """Test ClassificationResult Pydantic model."""
    result = ClassificationResult(
        item_id='tires_wheels',
        status='PASS',
        score=0.15,
        confidence=0.92,
        reasoning='Tires appear intact',
    )
    assert result.item_id == 'tires_wheels'
    assert result.status == 'PASS'
    assert result.score == 0.15
    assert result.confidence == 0.92


def test_classification_result_score_bounds() -> None:
    """Test score validation bounds."""
    with pytest.raises(ValueError):
        ClassificationResult(
            item_id='test',
            status='PASS',
            score=1.5,  # Invalid: > 1.0
            confidence=0.5,
        )

    with pytest.raises(ValueError):
        ClassificationResult(
            item_id='test',
            status='PASS',
            score=0.5,
            confidence=-0.1,  # Invalid: < 0.0
        )


def test_build_item_prompt() -> None:
    """Test prompt building for different items."""
    prompt = build_item_prompt('tires_wheels')
    assert 'Tires' in prompt or 'tires' in prompt.lower()
    assert 'PASS' in prompt
    assert 'MONITOR' in prompt
    assert 'FAIL' in prompt


def test_system_prompt_contains_instructions() -> None:
    """Test system prompt has required elements."""
    assert 'expert' in SYSTEM_PROMPT.lower()
    assert 'PASS' in SYSTEM_PROMPT
    assert 'MONITOR' in SYSTEM_PROMPT
    assert 'FAIL' in SYSTEM_PROMPT


def test_classifier_no_frames() -> None:
    """Test classifier handles empty frame list."""
    classifier = EquipmentClassifier()
    results = classifier.classify_all_items(frame_paths=[])

    # Should return UNKNOWN for all items
    for result in results.values():
        assert result.status == 'UNKNOWN'
        assert result.confidence == 0.0


@patch('src.vlm.gemini_client.GeminiClient.classify_image')
def test_classifier_mocked_response(mock_classify: MagicMock) -> None:
    """Test classifier with mocked Gemini response."""
    mock_classify.return_value = {
        'status': 'MONITOR',
        'score': 0.45,
        'confidence': 0.88,
        'reasoning': 'Some wear visible',
    }

    classifier = EquipmentClassifier()

    # Create a temporary test image path (would fail in real call)
    result = classifier.classify_frame(
        frame_path='/tmp/test.jpg',
        item_id='tires_wheels',
        use_fewshot=False,
    )

    assert result.status == 'MONITOR'
    assert result.score == 0.45
    assert result.confidence == 0.88


def test_classifier_error_handling() -> None:
    """Test classifier handles errors gracefully."""
    classifier = EquipmentClassifier()

    # Mock gemini to raise an exception
    classifier.gemini.classify_image = MagicMock(side_effect=Exception('API Error'))

    result = classifier.classify_frame(
        frame_path='/nonexistent/path.jpg',
        item_id='tires_wheels',
        use_fewshot=False,
    )

    # Should return UNKNOWN on error
    assert result.status == 'UNKNOWN'
    assert result.confidence == 0.0
    assert 'error' in result.reasoning.lower()
