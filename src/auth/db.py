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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS machines (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                vin TEXT NOT NULL,
                machine_type TEXT NOT NULL,
                niche TEXT NOT NULL,
                image_url TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inspection_reports (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                vin TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                summary_status TEXT NOT NULL,
                items_json TEXT NOT NULL,
                evidence_urls_json TEXT,
                report_json TEXT,
                narrative_text TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        _ensure_column(conn, 'inspection_reports', 'report_json', 'report_json TEXT')
        _ensure_column(conn, 'inspection_reports', 'narrative_text', 'narrative_text TEXT')
        conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cur = conn.execute(f'PRAGMA table_info({table})')
    columns = [row[1] for row in cur.fetchall()]
    if column not in columns:
        conn.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')


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


def create_machine(
    user_id: int,
    machine_id: str,
    name: str,
    vin: str,
    machine_type: str,
    niche: str,
    image_url: Optional[str],
    created_at: str,
    db_path: Optional[Path] = None,
) -> None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO machines (id, user_id, name, vin, machine_type, niche, image_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (machine_id, user_id, name, vin, machine_type, niche, image_url, created_at),
        )
        conn.commit()


def list_machines(user_id: int, db_path: Optional[Path] = None) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM machines WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return cur.fetchall()


def get_machine_by_id(
    user_id: int,
    machine_id: str,
    db_path: Optional[Path] = None,
) -> Optional[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM machines WHERE user_id = ? AND id = ?",
            (user_id, machine_id),
        )
        return cur.fetchone()


def get_latest_report_for_vin(
    user_id: int,
    vin: str,
    db_path: Optional[Path] = None,
) -> Optional[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT * FROM inspection_reports
            WHERE user_id = ? AND vin = ?
            ORDER BY observed_at DESC
            LIMIT 1
            """,
            (user_id, vin),
        )
        return cur.fetchone()


def list_reports(
    user_id: int,
    vin: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if vin:
            cur = conn.execute(
                """
                SELECT * FROM inspection_reports
                WHERE user_id = ? AND vin = ?
                ORDER BY observed_at DESC
                """,
                (user_id, vin),
            )
        else:
            cur = conn.execute(
                """
                SELECT * FROM inspection_reports
                WHERE user_id = ?
                ORDER BY observed_at DESC
                """,
                (user_id,),
            )
        return cur.fetchall()


def get_report_by_id(
    user_id: int,
    report_id: str,
    db_path: Optional[Path] = None,
) -> Optional[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM inspection_reports WHERE user_id = ? AND id = ?",
            (user_id, report_id),
        )
        return cur.fetchone()


def create_inspection_report(
    user_id: int,
    report_id: str,
    vin: str,
    observed_at: str,
    summary_status: str,
    items_json: str,
    evidence_urls_json: Optional[str],
    report_json: Optional[str],
    narrative_text: Optional[str],
    created_at: str,
    db_path: Optional[Path] = None,
) -> None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO inspection_reports (
                id, user_id, vin, observed_at, summary_status, items_json, evidence_urls_json, report_json, narrative_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                user_id,
                vin,
                observed_at,
                summary_status,
                items_json,
                evidence_urls_json,
                report_json,
                narrative_text,
                created_at,
            ),
        )
        conn.commit()
