from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.routes import require_user
from src.memory.supermemory_client import SupermemoryClient
from src.preferences.schema import (
    DEFAULT_PREFERENCES,
    InspectionPreferences,
    MachinePreferences,
    MachinePreferencesResponse,
    PreferencesResponse,
)

router = APIRouter(prefix='/preferences', tags=['preferences'])
memory_client = SupermemoryClient()


def _ensure_enabled() -> None:
    if not memory_client.api_key or not memory_client.base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Supermemory is not configured',
        )


def _merge_user_tags(user_id: int, tags: list[str]) -> list[str]:
    merged = list(tags)
    tag = f'user:{user_id}'
    if tag not in merged:
        merged.append(tag)
    return merged


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def _extract_updated_at(entry: Dict[str, Any]) -> Optional[datetime]:
    metadata = entry.get('metadata') if isinstance(entry, dict) else None
    content = entry.get('content') if isinstance(entry, dict) else None
    if isinstance(metadata, dict):
        ts = _parse_timestamp(metadata.get('updated_at'))
        if ts:
            return ts
    if isinstance(content, dict):
        ts = _parse_timestamp(content.get('updated_at'))
        if ts:
            return ts
    if isinstance(entry, dict):
        ts = _parse_timestamp(entry.get('created_at'))
        if ts:
            return ts
    return None


def _latest_entry(results: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not results:
        return None
    best = None
    best_ts = None
    for entry in results:
        ts = _extract_updated_at(entry)
        if ts and (best_ts is None or ts > best_ts):
            best = entry
            best_ts = ts
    return best or results[0]


def _load_preferences(tags: list[str], limit: int = 20) -> tuple[Optional[Dict[str, Any]], Optional[datetime]]:
    results = memory_client.search_memories(tags=tags, limit=limit)
    if not results:
        return None, None
    latest = _latest_entry(results)
    updated_at = _extract_updated_at(latest or {})
    return latest, updated_at


def _merge_preferences(
    base: InspectionPreferences,
    profile: Optional[InspectionPreferences],
    machine: Optional[MachinePreferences],
) -> InspectionPreferences:
    merged = base.model_dump()
    if profile:
        for key, value in profile.model_dump().items():
            merged[key] = value
    if machine:
        for key, value in machine.model_dump().items():
            if value is not None:
                merged[key] = value
    return InspectionPreferences(**merged)


def _parse_profile_preferences(entry: Dict[str, Any]) -> InspectionPreferences:
    content = entry.get('content', {}) if isinstance(entry, dict) else {}
    if not isinstance(content, dict):
        content = {}
    raw = content.get('preferences', content)
    return InspectionPreferences(**raw)


def _parse_machine_preferences(entry: Dict[str, Any]) -> MachinePreferences:
    content = entry.get('content', {}) if isinstance(entry, dict) else {}
    if not isinstance(content, dict):
        content = {}
    raw = content.get('preferences', content)
    return MachinePreferences(**raw)


@router.get('/profile', response_model=PreferencesResponse)
def get_profile_preferences(user=Depends(require_user)) -> PreferencesResponse:
    _ensure_enabled()
    tags = _merge_user_tags(user.id, ['kind:preferences', 'scope:profile'])
    entry, updated_at = _load_preferences(tags)
    if not entry:
        return PreferencesResponse(
            preferences=DEFAULT_PREFERENCES,
            effective_preferences=DEFAULT_PREFERENCES,
            updated_at=None,
            source='default',
        )
    prefs = _parse_profile_preferences(entry)
    return PreferencesResponse(
        preferences=prefs,
        effective_preferences=prefs,
        updated_at=updated_at,
        source='memory',
    )


@router.put('/profile', response_model=PreferencesResponse)
def update_profile_preferences(
    payload: InspectionPreferences,
    user=Depends(require_user),
) -> PreferencesResponse:
    _ensure_enabled()
    updated_at = datetime.now(timezone.utc).isoformat()
    content = {
        'preferences': payload.model_dump(),
        'updated_at': updated_at,
        'schema_version': 1,
    }
    metadata = {
        'scope': 'profile',
        'updated_at': updated_at,
        'schema_version': 1,
    }
    tags = _merge_user_tags(user.id, ['kind:preferences', 'scope:profile'])
    created = memory_client.create_memory(
        kind='preferences',
        content=content,
        tags=tags,
        metadata=metadata,
    )
    if not created:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Failed to save preferences')
    return PreferencesResponse(
        preferences=payload,
        effective_preferences=payload,
        updated_at=_parse_timestamp(updated_at),
        source='memory',
    )


@router.get('/machine/{vin}', response_model=MachinePreferencesResponse)
def get_machine_preferences(vin: str, user=Depends(require_user)) -> MachinePreferencesResponse:
    _ensure_enabled()
    profile_tags = _merge_user_tags(user.id, ['kind:preferences', 'scope:profile'])
    machine_tags = _merge_user_tags(user.id, ['kind:preferences', 'scope:machine', f'vin:{vin}'])

    profile_entry, _ = _load_preferences(profile_tags)
    machine_entry, machine_updated_at = _load_preferences(machine_tags)

    profile_prefs = _parse_profile_preferences(profile_entry) if profile_entry else None
    machine_prefs = _parse_machine_preferences(machine_entry) if machine_entry else None

    effective = _merge_preferences(DEFAULT_PREFERENCES, profile_prefs, machine_prefs)
    return MachinePreferencesResponse(
        preferences=machine_prefs or MachinePreferences(),
        effective_preferences=effective,
        updated_at=machine_updated_at,
        source='memory' if machine_entry else 'default',
    )


@router.put('/machine/{vin}', response_model=MachinePreferencesResponse)
def update_machine_preferences(
    vin: str,
    payload: MachinePreferences,
    user=Depends(require_user),
) -> MachinePreferencesResponse:
    _ensure_enabled()
    updated_at = datetime.now(timezone.utc).isoformat()
    content = {
        'preferences': payload.model_dump(),
        'updated_at': updated_at,
        'schema_version': 1,
    }
    metadata = {
        'scope': 'machine',
        'vin': vin,
        'updated_at': updated_at,
        'schema_version': 1,
    }
    tags = _merge_user_tags(user.id, ['kind:preferences', 'scope:machine', f'vin:{vin}'])
    created = memory_client.create_memory(
        kind='preferences',
        content=content,
        tags=tags,
        metadata=metadata,
    )
    if not created:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Failed to save preferences')

    profile_tags = _merge_user_tags(user.id, ['kind:preferences', 'scope:profile'])
    profile_entry, _ = _load_preferences(profile_tags)
    profile_prefs = _parse_profile_preferences(profile_entry) if profile_entry else None
    effective = _merge_preferences(DEFAULT_PREFERENCES, profile_prefs, payload)

    return MachinePreferencesResponse(
        preferences=payload,
        effective_preferences=effective,
        updated_at=_parse_timestamp(updated_at),
        source='memory',
    )
