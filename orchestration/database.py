# src/runbook_pipeline/sgdfsatabase.py
"""
Runbook Registry Database Module.
Maintained by the Data Engineering Team.
Provides a persistent storage layer in PostgreSQL to remember past incidents.
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Optional

# Local SQLite DB for the Runbook Registry
LOCAL_DB_PATH = Path(__file__).resolve().parents[2] / "runbook_registry_local.db"

def _load_env_file():
    """Loads environment variables from the .env file in the project root."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("'").strip('"')

class RunbookDB:
    def __init__(self):
        """Initializes the database connection (uses SQLite for local ease)."""
        _load_env_file()
        self.db_path = str(LOCAL_DB_PATH)
        self._create_tables()

    def get_connection(self):
        """Returns a connection to the local SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runbooks (
                    runbook_id TEXT PRIMARY KEY,
                    signal_type TEXT NOT NULL,
                    signal_summary TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    full_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_runbook(self, runbook) -> None:
        """Saves a successfully generated runbook into the local database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO runbooks 
                (runbook_id, signal_type, signal_summary, root_cause, owner, full_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                runbook.runbook_id,
                runbook.signal.signal_type,
                runbook.signal.summary,
                runbook.root_cause.root_cause,
                runbook.owner,
                runbook.model_dump_json()
            ))
            conn.commit()

    def get_historical_fix(self, signal_type: str, summary: str) -> Optional[dict]:
        """Searches the local database for a past runbook."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT full_json FROM runbooks 
                WHERE signal_type = ? AND signal_summary LIKE ?
                ORDER BY created_at DESC LIMIT 1
            ''', (signal_type, f"%{summary}%"))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row['full_json'])
        return None
