from __future__ import annotations

import base64
import os
import tempfile
from unittest.mock import MagicMock

import pytest

from src.corrections.fewshot import FewshotRetriever


def test_fewshot_retriever_no_config() -> None:
    """Test retriever gracefully handles missing config."""
    retriever = FewshotRetriever()
    # Mock missing API config
    retriever.memory.api_key = None
    retriever.memory.base_url = None

    examples = retriever.retrieve(item_id='tires_wheels')
    assert examples == []


def test_fewshot_retriever_empty_results() -> None:
    """Test retriever handles empty search results."""
    retriever = FewshotRetriever()
    retriever.memory.api_key = 'test'
    retriever.memory.base_url = 'http://test'
    retriever.memory.search_memories = MagicMock(return_value=[])

    examples = retriever.retrieve(item_id='tires_wheels', limit=3)
    assert examples == []


def test_fewshot_retriever_process_results() -> None:
    """Test processing of Supermemory results."""
    retriever = FewshotRetriever()

    # Create a temp frame file
    with tempfile.TemporaryDirectory() as tmpdir:
        retriever.frame_dir = tmpdir

        # Create a test image
        frame_hash = 'testhash123'
        frame_path = os.path.join(tmpdir, f'{frame_hash}.jpg')
        with open(frame_path, 'wb') as f:
            f.write(b'fake image data')

        results = [
            {
                'content': {
                    'item_id': 'tires_wheels',
                    'original': {'status': 'PASS', 'score': 0.15},
                    'corrected': {'status': 'MONITOR', 'score': 0.45},
                    'correction_notes': 'Visible wear',
                    'frame_sha256': frame_hash,
                }
            }
        ]

        examples = retriever._process_results(results)

        assert len(examples) == 1
        assert examples[0]['item_id'] == 'tires_wheels'
        assert examples[0]['corrected_status'] == 'MONITOR'
        assert 'image_base64' in examples[0]


def test_fewshot_retriever_missing_frame() -> None:
    """Test retriever skips results with missing frames."""
    retriever = FewshotRetriever()
    retriever.frame_dir = '/nonexistent/path'

    results = [
        {
            'content': {
                'item_id': 'tires_wheels',
                'corrected': {'status': 'FAIL', 'score': 0.75},
                'correction_notes': 'Missing frame',
                'frame_sha256': 'nonexistent_hash',
            }
        }
    ]

    examples = retriever._process_results(results)

    # Should skip results without accessible images
    assert len(examples) == 0


def test_fewshot_load_frame_image() -> None:
    """Test loading and base64 encoding of frame image."""
    retriever = FewshotRetriever()

    with tempfile.TemporaryDirectory() as tmpdir:
        retriever.frame_dir = tmpdir

        # Create test image
        test_data = b'test image content'
        frame_hash = 'abc123'
        frame_path = os.path.join(tmpdir, f'{frame_hash}.jpg')
        with open(frame_path, 'wb') as f:
            f.write(test_data)

        # Load and verify
        result = retriever._load_frame_image(frame_hash)

        assert result is not None
        decoded = base64.b64decode(result)
        assert decoded == test_data


def test_fewshot_load_frame_image_none() -> None:
    """Test loading with None hash."""
    retriever = FewshotRetriever()

    result = retriever._load_frame_image(None)
    assert result is None
