from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.auth.db import init_db


DB_PATH = Path('data') / 'catalyst.db'
USER_EMAIL = 'tejaswadhwa@gmail.com'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user_id(conn: sqlite3.Connection, email: str) -> int:
    cur = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f'User not found: {email}')
    return int(row[0])


def insert_machine(conn: sqlite3.Connection, user_id: int, name: str, vin: str, machine_type: str, niche: str, image_url: str) -> str:
    machine_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO machines (id, user_id, name, vin, machine_type, niche, image_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (machine_id, user_id, name, vin, machine_type, niche, image_url, now_iso()),
    )
    return machine_id


def insert_report(
    conn: sqlite3.Connection,
    user_id: int,
    vin: str,
    summary_status: str,
    items: list[dict],
    evidence_urls: list[str],
) -> str:
    report_id = str(uuid.uuid4())
    observed_at = now_iso()
    report_payload = {
        'vin': vin,
        'client_trace_id': report_id,
        'observed_at': observed_at,
        'summary': {'status': summary_status},
        'items': items,
    }
    conn.execute(
        """
        INSERT INTO inspection_reports (
            id, user_id, vin, observed_at, summary_status, items_json, evidence_urls_json, report_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            user_id,
            vin,
            observed_at,
            summary_status,
            json.dumps(items),
            json.dumps(evidence_urls),
            json.dumps(report_payload),
            observed_at,
        ),
    )
    return report_id


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        user_id = get_user_id(conn, USER_EMAIL)

        machines = [
            {
                'name': 'CAT 908M',
                'vin': '1HGCM82633A004352',
                'machine_type': 'wheel_loader',
                'niche': 'construction',
                'image_url': 'https://images.unsplash.com/photo-1466854076813-4aa9ac0fc347?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'name': 'CAT 320D',
                'vin': '2T1BURHE5JC109331',
                'machine_type': 'excavator',
                'niche': 'earthworks',
                'image_url': 'https://images.unsplash.com/photo-1509228627152-72ae9ae6848d?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'name': 'CAT D6T',
                'vin': '3GCPWCED5MG279184',
                'machine_type': 'dozer',
                'niche': 'mining',
                'image_url': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80',
            },
        ]

        for machine in machines:
            insert_machine(conn, user_id, **machine)

        reports = [
            {
                'vin': machines[0]['vin'],
                'summary_status': 'MONITOR',
                'items': [
                    {'id': 'hose_leak', 'status': 'MONITOR', 'notes': 'Minor seepage near hose clamp.'},
                    {'id': 'radiator_debris', 'status': 'PASS', 'notes': 'No visible debris.'},
                ],
                'evidence_urls': [
                    '/media/inspections/sample-1/frame-1.jpg',
                ],
            },
            {
                'vin': machines[1]['vin'],
                'summary_status': 'FAIL',
                'items': [
                    {'id': 'radiator_debris', 'status': 'FAIL', 'notes': 'Heavy debris in radiator fins.'},
                    {'id': 'hose_leak', 'status': 'MONITOR', 'notes': 'Slow drip observed.'},
                ],
                'evidence_urls': [
                    '/media/inspections/sample-2/frame-1.jpg',
                ],
            },
        ]

        for report in reports:
            insert_report(conn, user_id, **report)

        conn.commit()


if __name__ == '__main__':
    main()
