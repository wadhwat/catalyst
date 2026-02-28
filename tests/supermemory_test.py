from __future__ import annotations

import os
from pathlib import Path

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


_load_env_from_repo_root()

base_url = os.getenv('SUPERMEMORY_BASE_URL') or os.getenv('SUPERMEMORY_API_URL')
if base_url:
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'https://{base_url}'
else:
    base_url = 'https://api.supermemory.ai'

if base_url.rstrip('/').endswith('/v3'):
    base_url = base_url.rstrip('/')
    base_url = base_url[: -len('/v3')]

os.environ['SUPERMEMORY_BASE_URL'] = base_url
os.environ['SUPERMEMORY_API_URL'] = base_url

client = Supermemory(base_url=base_url) if base_url else Supermemory()

# Add a memory
client.add(
    content="User prefers dark mode",
    container_tags=["user-123"],
)

# Search memories
results = client.search.documents(
    q="dark mode",
    container_tags=["user-123"],
)
