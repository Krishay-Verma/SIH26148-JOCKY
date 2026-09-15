"""
SQLite persistence for JOCKY investigations.

Stores one row per investigation run: an id, name, endpoint, timestamps,
and the full report as a JSON text blob. This is intentionally a single
flat table rather than a normalized schema - for the MVP, a report is
naturally one document, and splitting it into multiple tables would add
complexity with no real benefit yet.

Uses the standard library's sqlite3 module directly (no ORM) - the
queries here are simple enough that an ORM would add ceremony without
adding clarity.
"""

import json
import sqlite3
from pathlib import Path

_DB_PATH = Path("jocky.db")


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the JOCKY database.

    row_factory=sqlite3.Row lets us access columns by name (row["id"])
    instead of by numeric index, which is much easier to read.
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the investigations table if it doesn't already exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investigation_name TEXT NOT NULL,
                endpoint_hostname TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                findings_count INTEGER NOT NULL,
                report_json TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_investigation(
    investigation_name: str,
    endpoint_hostname: str,
    started_at: str,
    finished_at: str,
    findings_count: int,
    report: dict,
) -> int:
    """Insert one investigation record. Returns the new row's id."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO investigations
                (investigation_name, endpoint_hostname, started_at,
                 finished_at, findings_count, report_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                investigation_name,
                endpoint_hostname,
                started_at,
                finished_at,
                findings_count,
                json.dumps(report),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def list_investigations() -> list[dict]:
    """Return summary info (no full report) for every stored investigation, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT id, investigation_name, endpoint_hostname,
                   started_at, finished_at, findings_count
            FROM investigations
            ORDER BY id DESC
        """).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_investigation(investigation_id: int) -> dict | None:
    """Return the full record (including report_json) for one investigation, or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM investigations WHERE id = ?",
            (investigation_id,),
        ).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["report_json"] = json.loads(record["report_json"])
        return record
    finally:
        conn.close()