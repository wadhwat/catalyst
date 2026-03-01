from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


def _get_model() -> str:
    return os.getenv('OPENAI_MODEL', 'gpt-4o')


NARRATIVE_RESPONSE_SCHEMA = {
    'type': 'json_schema',
    'json_schema': {
        'name': 'inspection_narrative',
        'strict': True,
        'schema': {
            'type': 'object',
            'properties': {
                'narrative': {'type': 'string'},
            },
            'required': ['narrative'],
            'additionalProperties': False,
        },
    },
}


def _summarize_history(report: Dict[str, Any]) -> Dict[str, Any]:
    items = report.get('items') or []
    failed_items = [item.get('id') for item in items if item.get('status') != 'PASS']
    return {
        'observed_at': report.get('observed_at'),
        'status': (report.get('summary') or {}).get('status'),
        'failed_items': [item for item in failed_items if item],
    }


async def build_narrative(
    current_report: Dict[str, Any],
    history_reports: List[Dict[str, Any]],
) -> str:
    history_summary = [_summarize_history(report) for report in history_reports]
    payload = {
        'current_report': {
            'observed_at': current_report.get('observed_at'),
            'summary': current_report.get('summary'),
            'items': current_report.get('items'),
        },
        'history': history_summary,
    }

    try:
        response = await _get_client().chat.completions.create(
            model=_get_model(),
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are writing a concise inspection narrative for a fleet manager. '
                        'Summarize current checklist failures and explain why they matter. '
                        'If history is provided, note progression over time. '
                        'Keep it readable and under 180 words. Return only JSON.'
                    ),
                },
                {'role': 'user', 'content': json.dumps(payload)},
            ],
            response_format=NARRATIVE_RESPONSE_SCHEMA,
            temperature=0.2,
            max_tokens=256,
        )
        raw = response.choices[0].message.content
        if not raw:
            return ''
        parsed = json.loads(raw)
        narrative = parsed.get('narrative', '')
        return narrative.strip()
    except Exception as exc:
        logger.warning('Narrative generation failed: %s', exc)
        return ''
