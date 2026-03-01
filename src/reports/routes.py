from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth import db
from src.auth.routes import require_user

router = APIRouter(prefix='/reports', tags=['reports'])


def _row_to_report(row) -> dict:
    report_json = row['report_json']
    if report_json:
        try:
            return json.loads(report_json)
        except Exception:
            pass

    try:
        items = json.loads(row['items_json'] or '[]')
    except Exception:
        items = []
    evidence_urls = []
    try:
        evidence_urls = json.loads(row['evidence_urls_json'] or '[]')
    except Exception:
        evidence_urls = []
    for item in items:
        if 'evidence_urls' not in item:
            item['evidence_urls'] = evidence_urls
    return {
        'vin': row['vin'],
        'client_trace_id': row['id'],
        'observed_at': row['observed_at'],
        'summary': {
            'status': row['summary_status'],
            'notes': None,
        },
        'items': items,
    }


@router.get('', response_model=List[dict])
def list_reports(
    vin: Optional[str] = Query(default=None),
    user=Depends(require_user),
) -> List[dict]:
    rows = db.list_reports(user.id, vin=vin)
    return [_row_to_report(row) for row in rows]


@router.get('/{report_id}', response_model=dict)
def get_report(report_id: str, user=Depends(require_user)) -> dict:
    row = db.get_report_by_id(user.id, report_id)
    if not row:
        raise HTTPException(status_code=404, detail='Report not found')
    return _row_to_report(row)
