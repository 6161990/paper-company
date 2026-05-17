import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "paper_company.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                markdown_path TEXT,
                content_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brief_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                source TEXT,
                url TEXT,
                category TEXT,
                hook TEXT,
                why_now TEXT,
                why_fit TEXT,
                next_action TEXT,
                expansion TEXT,
                exploration_path TEXT,
                score REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (brief_id) REFERENCES briefs(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                brief_id INTEGER,
                feedback_type TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (brief_id) REFERENCES briefs(id)
            );

            CREATE TABLE IF NOT EXISTS mobile_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                input_text TEXT NOT NULL,
                response_text TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS incident_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symptom TEXT NOT NULL,
                context TEXT,
                suspected_causes TEXT,
                checklist TEXT,
                sources TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


def save_brief_record(
    *,
    run_date: str,
    title: str,
    content: str,
    markdown_path: Path,
    content_hash: str,
) -> int:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO briefs (
                run_date, title, content, markdown_path, content_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_date) DO UPDATE SET
                title = excluded.title,
                content = excluded.content,
                markdown_path = excluded.markdown_path,
                content_hash = excluded.content_hash,
                updated_at = excluded.updated_at
            """,
            (run_date, title, content, str(markdown_path), content_hash, now, now),
        )
        row = conn.execute("SELECT id FROM briefs WHERE run_date = ?", (run_date,)).fetchone()
        if row is None:
            raise RuntimeError(f"Failed to save brief for {run_date}")
        return int(row["id"])

