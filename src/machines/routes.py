from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth import db
from src.auth.routes import require_user

router = APIRouter(prefix='/machines', tags=['machines'])


class MachineCreateRequest(BaseModel):
    name: str
    vin: str
    machine_type: str
    niche: str
    image_url: Optional[str] = None


class MachineResponse(BaseModel):
    id: str
    name: str
    vin: str
    machineType: str
    niche: str
    imageUrl: Optional[str] = None
    lastInspectedMs: Optional[int] = None
    status: str
    criticalIssues: int
    criticalIssueLabels: List[str] = Field(default_factory=list)
    componentIssues: List[Dict[str, Any]] = Field(default_factory=list)


def _parse_time_ms(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _build_report_summary(row) -> tuple[Optional[int], str, List[str], List[Dict[str, Any]]]:
    if not row:
        return None, 'UNKNOWN', [], []
    last_inspected = _parse_time_ms(row['observed_at'])
    status = row['summary_status'] or 'UNKNOWN'
    try:
        items = json.loads(row['items_json'] or '[]')
    except Exception:
        items = []
    critical_labels = [item.get('id') for item in items if item.get('status') == 'FAIL']
    component_counts: Dict[str, int] = {}
    for item in items:
        component = item.get('id')
        if not component:
            continue
        if item.get('status') == 'PASS':
            continue
        component_counts[component] = component_counts.get(component, 0) + 1
    component_issues = [
        {'component': key, 'count': count} for key, count in component_counts.items()
    ]
    return last_inspected, status, critical_labels, component_issues


@router.get('', response_model=List[MachineResponse])
def list_machines(user=Depends(require_user)) -> List[MachineResponse]:
    rows = db.list_machines(user.id)
    response: List[MachineResponse] = []
    for row in rows:
        latest_report = db.get_latest_report_for_vin(user.id, row['vin'])
        last_inspected, status, critical_labels, component_issues = _build_report_summary(
            latest_report
        )
        response.append(
            MachineResponse(
                id=row['id'],
                name=row['name'],
                vin=row['vin'],
                machineType=row['machine_type'],
                niche=row['niche'],
                imageUrl=row['image_url'],
                lastInspectedMs=last_inspected,
                status=status,
                criticalIssues=len(critical_labels),
                criticalIssueLabels=critical_labels,
                componentIssues=component_issues,
            )
        )
    return response


@router.post('', response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreateRequest, user=Depends(require_user)) -> MachineResponse:
    machine_id = str(__import__('uuid').uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    db.create_machine(
        user_id=user.id,
        machine_id=machine_id,
        name=payload.name.strip(),
        vin=payload.vin.strip(),
        machine_type=payload.machine_type.strip(),
        niche=payload.niche.strip(),
        image_url=payload.image_url,
        created_at=created_at,
    )
    return MachineResponse(
        id=machine_id,
        name=payload.name.strip(),
        vin=payload.vin.strip(),
        machineType=payload.machine_type.strip(),
        niche=payload.niche.strip(),
        imageUrl=payload.image_url,
        lastInspectedMs=None,
        status='UNKNOWN',
        criticalIssues=0,
        criticalIssueLabels=[],
        componentIssues=[],
    )


@router.get('/{machine_id}', response_model=MachineResponse)
def get_machine(machine_id: str, user=Depends(require_user)) -> MachineResponse:
    row = db.get_machine_by_id(user.id, machine_id)
    if not row:
        raise HTTPException(status_code=404, detail='Machine not found')
    latest_report = db.get_latest_report_for_vin(user.id, row['vin'])
    last_inspected, status, critical_labels, component_issues = _build_report_summary(
        latest_report
    )
    return MachineResponse(
        id=row['id'],
        name=row['name'],
        vin=row['vin'],
        machineType=row['machine_type'],
        niche=row['niche'],
        imageUrl=row['image_url'],
        lastInspectedMs=last_inspected,
        status=status,
        criticalIssues=len(critical_labels),
        criticalIssueLabels=critical_labels,
        componentIssues=component_issues,
    )
