from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.auth import db
from src.auth.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password('s3cret-pass')
    assert verify_password('s3cret-pass', hashed)
    assert not verify_password('wrong-pass', hashed)


def test_token_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('JWT_SECRET', 'test-secret-32-bytes-minimum-OK!!')
    token = create_access_token({'sub': '123'})
    payload = decode_access_token(token)
    assert payload['sub'] == '123'


def test_user_create_and_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('CATALYST_DB_PATH', str(db_path))
    db.init_db()

    user_id = db.create_user(
        email='user@example.com',
        password_hash=hash_password('p@ssword1'),
        display_name='Test User',
        created_at='2025-01-01T00:00:00+00:00',
    )
    row = db.get_user_by_email('user@example.com')
    assert row is not None
    assert row['id'] == user_id
    assert row['display_name'] == 'Test User'
