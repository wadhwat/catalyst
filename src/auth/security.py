from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def _b64decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return f'{_b64encode(salt)}${_b64encode(dk)}'


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, dk_b64 = stored.split('$', 1)
    except ValueError:
        return False
    salt = _b64decode(salt_b64)
    expected = _b64decode(dk_b64)
    candidate = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return hmac.compare_digest(candidate, expected)


def _jwt_secret() -> str:
    return os.getenv('JWT_SECRET', 'dev-secret')


def _jwt_exp_minutes() -> int:
    try:
        return int(os.getenv('JWT_EXPIRE_MINUTES', '60'))
    except ValueError:
        return 60


def create_access_token(payload: Dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_jwt_exp_minutes())
    to_encode = dict(payload)
    to_encode['exp'] = expire
    return jwt.encode(to_encode, _jwt_secret(), algorithm='HS256')


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=['HS256'])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expired',
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
        ) from exc
