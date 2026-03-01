from __future__ import annotations

import json
import logging
import os
from typing import List

from openai import AsyncOpenAI

from src.inspection.schema import Finding
from src.report.schema import Report, ReportItem, ReportSummary

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


def _get_model() -> str:
    return os.getenv('OPENAI_MODEL', 'gpt-4o')


REPORT_RESPONSE_SCHEMA = {
    'type': 'json_schema',
    'json_schema': {
        'name': 'inspection_report',
        'strict': True,
        'schema': {
            'type': 'object',
            'properties': {
                'summary': {
                    'type': 'object',
                    'properties': {
                        'status': {
                            'type': 'string',
                            'enum': ['PASS', 'MONITOR', 'FAIL'],
                        },
                        'notes': {'type': 'string'},
                    },
                    'required': ['status', 'notes'],
                    'additionalProperties': False,
                },
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'status': {
                                'type': 'string',
                                'enum': ['PASS', 'MONITOR', 'FAIL'],
                            },
                            'notes': {'type': 'string'},
                            'evidence': {
                                'type': 'array',
                                'items': {'type': 'string'},
                            },
                            'score': {'type': 'number'},
                        },
                        'required': ['id', 'status', 'notes', 'evidence'],
                        'additionalProperties': False,
                    },
                },
            },
            'required': ['summary', 'items'],
            'additionalProperties': False,
        },
    },
}


def _normalize_report(report: Report, draft: Report, evidence_urls: List[str]) -> Report:
    draft_map = {item.id: item for item in draft.items}
    reviewed_map = {item.id: item for item in report.items}
    items: List[ReportItem] = []
    for item in draft.items:
        reviewed = reviewed_map.get(item.id, item)
        if not reviewed.evidence:
            reviewed = reviewed.model_copy(update={'evidence': item.evidence or evidence_urls})
        items.append(reviewed)
    summary = report.summary or draft.summary
    if not summary.notes:
        summary = ReportSummary(status=summary.status, notes=draft.summary.notes or '')
    return Report(summary=summary, items=items)


async def review_report(
    findings: List[Finding],
    draft_report: Report,
    evidence_urls: List[str],
) -> Report:
    if not findings:
        return draft_report

    payload = {
        'findings': [finding.model_dump() for finding in findings],
        'draft_report': draft_report.model_dump(),
    }

    try:
        response = await _get_client().chat.completions.create(
            model=_get_model(),
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an expert heavy-equipment inspector. '
                        'Review the draft report using the VLM findings. '
                        'Keep the same item ids from the draft and ensure all '
                        'items are present. Adjust statuses/notes if needed. '
                        'Return only JSON matching the schema.'
                    ),
                },
                {
                    'role': 'user',
                    'content': json.dumps(payload),
                },
            ],
            response_format=REPORT_RESPONSE_SCHEMA,
            temperature=0.1,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content
        if not raw:
            return draft_report
        parsed = json.loads(raw)
        reviewed = Report(**parsed)
        return _normalize_report(reviewed, draft_report, evidence_urls)
    except Exception as exc:
        logger.warning('LLM report review failed: %s', exc)
        return draft_report
