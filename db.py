import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

DB_PATH = os.environ.get("WORLDGATE_DB", "worldgate.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            documents TEXT NOT NULL,
            mismatches TEXT NOT NULL,
            missing_fields TEXT NOT NULL,
            result TEXT NOT NULL
        )
        """
    )
    return conn


def save_check(documents_checked, mismatches, missing_fields, result) -> int:
    with closing(connect()) as conn:
        with conn:
            cursor = conn.execute(
                "INSERT INTO checks (created_at, documents, mismatches, missing_fields, result) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(documents_checked),
                    json.dumps(mismatches),
                    json.dumps(missing_fields),
                    result,
                ),
            )
        return cursor.lastrowid


def list_checks():
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT id, created_at, result, mismatches, missing_fields "
            "FROM checks ORDER BY id DESC"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "result": row["result"],
            "mismatch_count": len(json.loads(row["mismatches"])),
            "missing_count": len(json.loads(row["missing_fields"])),
        }
        for row in rows
    ]


def get_check(check_id: int):
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM checks WHERE id = ?", (check_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "documents_checked": json.loads(row["documents"]),
        "mismatches": json.loads(row["mismatches"]),
        "missing_fields": json.loads(row["missing_fields"]),
        "result": row["result"],
    }