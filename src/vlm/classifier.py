from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from src.report.generate_baseline import ITEM_IDS
from src.vlm.gemini_client import GeminiClient
from src.vlm.prompts import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_item_prompt
from src.vlm.schema import ClassificationResult

if TYPE_CHECKING:
    from src.corrections.fewshot import FewshotRetriever

logger = logging.getLogger(__name__)


class EquipmentClassifier:
    """Orchestrates VLM-based equipment classification."""

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        fewshot_retriever: Optional['FewshotRetriever'] = None,
    ) -> None:
        self.gemini = gemini_client or GeminiClient()
        self._fewshot = fewshot_retriever

    @property
    def fewshot(self) -> Optional['FewshotRetriever']:
        """Lazy load fewshot retriever to avoid circular imports."""
        if self._fewshot is None:
            try:
                from src.corrections.fewshot import FewshotRetriever

                self._fewshot = FewshotRetriever()
            except ImportError:
                logger.warning('FewshotRetriever not available')
        return self._fewshot

    def classify_frame(
        self,
        frame_path: str,
        item_id: str,
        vin: Optional[str] = None,
        user_id: Optional[int] = None,
        use_fewshot: bool = True,
    ) -> ClassificationResult:
        """Classify a single frame for a specific item."""
        examples: List[Dict] = []

        if use_fewshot and self.fewshot:
            examples = self.fewshot.retrieve(
                item_id=item_id,
                vin=vin,
                user_id=user_id,
                limit=3,
            )

        try:
            if examples:
                result = self.gemini.classify_with_fewshot(
                    image_path=frame_path,
                    system_prompt=SYSTEM_PROMPT,
                    examples=examples,
                    item_id=item_id,
                )
            else:
                prompt = f'{SYSTEM_PROMPT}\n\n{build_item_prompt(item_id)}'
                result = self.gemini.classify_image(
                    image_path=frame_path,
                    prompt=prompt,
                    response_schema=RESPONSE_SCHEMA,
                )

            return ClassificationResult(
                item_id=item_id,
                status=result.get('status', 'UNKNOWN'),
                score=float(result.get('score', 0.5)),
                confidence=float(result.get('confidence', 0.0)),
                reasoning=result.get('reasoning'),
            )
        except Exception as exc:
            logger.error('Classification failed for %s: %s', item_id, exc)
            # Return neutral result on error
            return ClassificationResult(
                item_id=item_id,
                status='UNKNOWN',
                score=0.5,
                confidence=0.0,
                reasoning=f'Classification error: {exc}',
            )

    def classify_all_items(
        self,
        frame_paths: List[str],
        vin: Optional[str] = None,
        user_id: Optional[int] = None,
        use_fewshot: bool = True,
    ) -> Dict[str, ClassificationResult]:
        """Classify all equipment items using available frames."""
        results: Dict[str, ClassificationResult] = {}

        if not frame_paths:
            logger.warning('No frames provided for classification')
            # Return unknown results for all items
            for item_id in ITEM_IDS:
                results[item_id] = ClassificationResult(
                    item_id=item_id,
                    status='UNKNOWN',
                    score=0.5,
                    confidence=0.0,
                    reasoning='No frames available for classification',
                )
            return results

        # Use first frame for now; could be enhanced to use multiple frames
        primary_frame = frame_paths[0]

        for item_id in ITEM_IDS:
            results[item_id] = self.classify_frame(
                frame_path=primary_frame,
                item_id=item_id,
                vin=vin,
                user_id=user_id,
                use_fewshot=use_fewshot,
            )

        return results
