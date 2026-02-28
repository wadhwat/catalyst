from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional


def get_db_path() -> Path:
    value = os.getenv('CATALYST_DB_PATH')
    if value:
        return Path(value)
    return Path('data') / 'catalyst.db'


def init_db(db_path: Optional[Path] = None) -> None:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_user(
    email: str,
    password_hash: str,
    display_name: Optional[str],
    created_at: str,
    db_path: Optional[Path] = None,
) -> int:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO users (email, password_hash, display_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (email, password_hash, display_name, created_at),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_user_by_email(email: str, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cur.fetchone()


def get_user_by_id(user_id: int, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()


def update_display_name(
    user_id: int,
    display_name: Optional[str],
    db_path: Optional[Path] = None,
) -> None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE users SET display_name = ? WHERE id = ?",
            (display_name, user_id),
        )
        conn.commit()
