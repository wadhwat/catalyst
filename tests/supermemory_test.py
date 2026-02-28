from __future__ import annotations

import os
from pathlib import Path

import pytest
from supermemory import Supermemory


def _load_env_from_repo_root() -> None:
    if os.getenv('SUPERMEMORY_API_KEY'):
        return
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def _client() -> Supermemory:
    run_live = os.getenv('SUPERMEMORY_RUN_LIVE_TESTS', '').lower() in {'1', 'true', 'yes'}
    if not run_live:
        pytest.skip('Live Supermemory tests disabled (set SUPERMEMORY_RUN_LIVE_TESTS=1)')
    _load_env_from_repo_root()
    api_key = os.getenv('SUPERMEMORY_API_KEY')
    if not api_key or not api_key.strip():
        pytest.skip('SUPERMEMORY_API_KEY not set')
    base_url = os.getenv('SUPERMEMORY_BASE_URL') or os.getenv('SUPERMEMORY_API_URL')
    if base_url:
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'https://{base_url}'
        if base_url.rstrip('/').endswith('/v3'):
            base_url = base_url.rstrip('/')
            base_url = base_url[: -len('/v3')]
    return Supermemory(api_key=api_key, base_url=base_url)


def test_supermemory_add_and_search() -> None:
    client = _client()
    content = "User prefers dark mode"
    tag = "user-123"
    client.add(content=content, container_tags=[tag])
    results = client.search.documents(q="dark mode", container_tags=[tag], limit=5)
    assert results.results
