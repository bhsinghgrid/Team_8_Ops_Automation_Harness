import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).parent.parent / "data" / "activity_results.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            activity_id TEXT,
            activity_name TEXT,
            result_json TEXT,
            received_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_activity(workflow_id: str, activity_id: str, activity_name: str, result: Dict[str, Any], received_at: str) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activities (workflow_id, activity_id, activity_name, result_json, received_at) VALUES (?, ?, ?, ?, ?)",
        (workflow_id, activity_id, activity_name, json.dumps(result), received_at),
    )
    conn.commit()
    row_id = cur.lastrowid
    cur.execute("SELECT * FROM activities WHERE id = ?", (row_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}
    return {
        "id": row["id"],
        "workflow_id": row["workflow_id"],
        "activity_id": row["activity_id"],
        "activity_name": row["activity_name"],
        "result": json.loads(row["result_json"] or "{}"),
        "received_at": row["received_at"],
    }


def get_activities_for_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities WHERE workflow_id = ? ORDER BY id ASC", (workflow_id,))
    rows = cur.fetchall()
    conn.close()
    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "activity_id": row["activity_id"],
                "activity_name": row["activity_name"],
                "result": json.loads(row["result_json"] or "{}"),
                "received_at": row["received_at"],
            }
        )
    return results
