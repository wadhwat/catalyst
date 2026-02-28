from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class SupermemoryClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        workspace: Optional[str] = None,
        timeout_s: int = 10,
    ) -> None:
        self.api_key = api_key or os.getenv('SUPERMEMORY_API_KEY')
        self.base_url = (base_url or os.getenv('SUPERMEMORY_BASE_URL') or '').rstrip('/')
        self.workspace = workspace or os.getenv('SUPERMEMORY_WORKSPACE')
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        if self.workspace:
            headers['X-Workspace'] = self.workspace
        return headers

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        if not self.base_url:
            logger.error('SUPERMEMORY_BASE_URL is not set')
            return None
        if not self.api_key:
            logger.error('SUPERMEMORY_API_KEY is not set')
            return None

        url = f'{self.base_url}{path}'
        data = None
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')

        req = Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode('utf-8')
                if not body:
                    return None
                return json.loads(body)
        except HTTPError as exc:
            try:
                detail = exc.read().decode('utf-8')
            except Exception:
                detail = str(exc)
            logger.error('Supermemory API error %s: %s', exc.code, detail)
            return None
        except URLError as exc:
            logger.error('Supermemory request failed: %s', exc)
            return None

    def health(self) -> bool:
        path = os.getenv('SUPERMEMORY_HEALTH_PATH', '/health')
        result = self._request('GET', path)
        return bool(result)

    def create_memory(
        self,
        kind: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        path = os.getenv('SUPERMEMORY_CREATE_PATH', '/memories')
        payload: Dict[str, Any] = {'type': kind, 'content': content}
        if tags:
            payload['tags'] = tags
        if metadata:
            payload['metadata'] = metadata
        return self._request('POST', path, payload)

    def search_memories(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        path = os.getenv('SUPERMEMORY_SEARCH_PATH', '/memories/search')
        payload: Dict[str, Any] = {'limit': limit}
        if query:
            payload['query'] = query
        if tags:
            payload['tags'] = tags
        if metadata:
            payload['metadata'] = metadata
        result = self._request('POST', path, payload)
        if isinstance(result, dict) and 'results' in result:
            return result['results'] or []
        if isinstance(result, list):
            return result
        return []

