from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini Vision API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = 'gemini-2.0-flash',
    ) -> None:
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model = model
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            if not self.api_key:
                raise ValueError('GOOGLE_API_KEY not set')
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError('google-genai package is required. Install with: pip install google-genai')
        return self._client

    def classify_image(
        self,
        image_path: str,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Classify an image using Gemini vision model."""
        from google.genai import types

        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Detect mime type from extension
        ext = os.path.splitext(image_path.lower())[1]
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        contents = [
            types.Content(
                role='user',
                parts=[
                    types.Part(text=prompt),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_data,
                        )
                    ),
                ],
            )
        ]

        config = types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for consistent classification
            response_mime_type='application/json',
        )
        if response_schema:
            config.response_schema = response_schema

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        return json.loads(response.text)

    def classify_with_fewshot(
        self,
        image_path: str,
        system_prompt: str,
        examples: List[Dict[str, Any]],
        item_id: str,
    ) -> Dict[str, Any]:
        """Classify with few-shot examples from corrections."""
        from google.genai import types

        contents = []

        # Add system context
        contents.append(
            types.Content(
                role='user',
                parts=[types.Part(text=system_prompt)],
            )
        )

        # Add few-shot examples
        for example in examples:
            # User turn: show image and ask for classification
            contents.append(
                types.Content(
                    role='user',
                    parts=[
                        types.Part(text=f"Classify this {item_id.replace('_', ' ')} image:"),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type='image/jpeg',
                                data=base64.b64decode(example['image_base64']),
                            )
                        ),
                    ],
                )
            )
            # Model turn: show correct answer
            contents.append(
                types.Content(
                    role='model',
                    parts=[
                        types.Part(
                            text=json.dumps(
                                {
                                    'status': example['corrected_status'],
                                    'score': example['corrected_score'],
                                    'reasoning': example['correction_notes'],
                                }
                            )
                        )
                    ],
                )
            )

        # Add current image
        with open(image_path, 'rb') as f:
            image_data = f.read()

        contents.append(
            types.Content(
                role='user',
                parts=[
                    types.Part(text=f"Now classify this {item_id.replace('_', ' ')} image:"),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type='image/jpeg',
                            data=image_data,
                        )
                    ),
                ],
            )
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type='application/json',
            ),
        )

        return json.loads(response.text)
