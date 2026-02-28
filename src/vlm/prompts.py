from __future__ import annotations

from src.report.generate_baseline import NOTES

SYSTEM_PROMPT = """You are an expert heavy equipment inspector for Caterpillar machinery.
Your task is to analyze images and classify the condition of specific equipment components.

For each component, provide:
1. status: PASS (good condition), MONITOR (needs attention), or FAIL (requires immediate action)
2. score: A severity score from 0.0 (perfect) to 1.0 (critical failure)
   - PASS: 0.0-0.29
   - MONITOR: 0.3-0.59
   - FAIL: 0.6-1.0
3. confidence: How confident you are in this assessment (0.0-1.0)
4. reasoning: Brief explanation of your assessment

Be conservative - when in doubt, escalate the severity."""


def build_item_prompt(item_id: str) -> str:
    """Build classification prompt for a specific item."""
    item_notes = NOTES.get(item_id, {})
    item_name = item_id.replace('_', ' ').title()

    return f"""Analyze the image and classify the condition of: {item_name}

Classification criteria:
- PASS: {item_notes.get('PASS', 'Component appears in good working condition')}
- MONITOR: {item_notes.get('MONITOR', 'Component shows signs of wear requiring attention')}
- FAIL: {item_notes.get('FAIL', 'Component requires immediate repair or replacement')}

Respond with JSON:
{{
  "status": "PASS" | "MONITOR" | "FAIL",
  "score": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "reasoning": "<brief explanation>"
}}"""


RESPONSE_SCHEMA = {
    'type': 'object',
    'properties': {
        'status': {'type': 'string', 'enum': ['PASS', 'MONITOR', 'FAIL']},
        'score': {'type': 'number', 'minimum': 0.0, 'maximum': 1.0},
        'confidence': {'type': 'number', 'minimum': 0.0, 'maximum': 1.0},
        'reasoning': {'type': 'string'},
    },
    'required': ['status', 'score', 'confidence', 'reasoning'],
}
