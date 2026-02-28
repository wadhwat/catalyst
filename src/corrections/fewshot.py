from __future__ import annotations

import base64
import logging
import os
from typing import Any, Dict, List, Optional

from src.memory.supermemory_client import SupermemoryClient

logger = logging.getLogger(__name__)


class FewshotRetriever:
    """Retrieves correction examples for few-shot prompting."""

    def __init__(
        self,
        memory_client: Optional[SupermemoryClient] = None,
        frame_storage_dir: Optional[str] = None,
    ) -> None:
        self.memory = memory_client or SupermemoryClient()
        self.frame_dir = frame_storage_dir or os.getenv('FRAME_STORAGE_DIR', '/tmp/catalyst_frames')

    def retrieve(
        self,
        item_id: str,
        vin: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve few-shot examples from past corrections."""
        if not self.memory.api_key or not self.memory.base_url:
            logger.warning('Supermemory not configured; skipping few-shot retrieval')
            return []

        # Build query tags
        tags = [
            f'item:{item_id}',
            'kind:classification_correction',
        ]

        examples: List[Dict[str, Any]] = []

        # First try VIN-specific corrections (most relevant)
        if vin:
            vin_results = self.memory.search_memories(
                tags=[*tags, f'vin:{vin}'],
                limit=limit,
            )
            examples.extend(self._process_results(vin_results))

        # Fill remaining slots with general corrections for this item type
        if len(examples) < limit:
            remaining = limit - len(examples)
            general_results = self.memory.search_memories(
                query=f'{item_id} classification correction',
                tags=tags,
                limit=remaining,
            )
            examples.extend(self._process_results(general_results))

        return examples[:limit]

    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process Supermemory results into few-shot examples."""
        examples = []

        for result in results:
            content = result.get('content', {})

            # Try to load the referenced frame image
            frame_sha256 = content.get('frame_sha256')
            image_base64 = self._load_frame_image(frame_sha256)

            if not image_base64:
                # Skip examples without accessible images
                continue

            examples.append(
                {
                    'item_id': content.get('item_id'),
                    'original_status': content.get('original', {}).get('status'),
                    'original_score': content.get('original', {}).get('score'),
                    'corrected_status': content.get('corrected', {}).get('status'),
                    'corrected_score': content.get('corrected', {}).get('score'),
                    'correction_notes': content.get('correction_notes'),
                    'image_base64': image_base64,
                }
            )

        return examples

    def _load_frame_image(self, frame_sha256: Optional[str]) -> Optional[str]:
        """Load frame image by SHA256 hash and return base64."""
        if not frame_sha256:
            return None

        # Look for frame in storage directory
        # Files are stored as {sha256}.jpg
        frame_path = os.path.join(self.frame_dir, f'{frame_sha256}.jpg')

        if not os.path.exists(frame_path):
            logger.debug('Frame not found: %s', frame_path)
            return None

        try:
            with open(frame_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as exc:
            logger.warning('Failed to load frame %s: %s', frame_path, exc)
            return None
