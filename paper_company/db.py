import os
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
# Railway: /data (Volume), Local: ./data
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "data" / "paper_company.db"))


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
                status TEXT NOT NULL DEFAULT 'candidate',
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

            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_ms INTEGER,
                returncode INTEGER,
                stdout TEXT,
                stderr TEXT,
                error TEXT
            );

            """
        )
        conn.commit()

        cols = {r[1] for r in conn.execute("PRAGMA table_info(items)")}
        if "status" not in cols:
            conn.execute(
                "ALTER TABLE items ADD COLUMN status TEXT NOT NULL DEFAULT 'candidate'"
            )
            conn.commit()


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


def replace_items(brief_id: int, items: list[dict]) -> None:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute("DELETE FROM items WHERE brief_id = ?", (brief_id,))
        conn.executemany(
            """
            INSERT INTO items (
                brief_id,
                title,
                source,
                url,
                category,
                hook,
                why_now,
                why_fit,
                next_action,
                expansion,
                exploration_path,
                score,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    brief_id,
                    item.get("title") or "Untitled",
                    item.get("source"),
                    item.get("url"),
                    item.get("category"),
                    item.get("hook"),
                    item.get("why_now"),
                    item.get("why_fit"),
                    item.get("next_action"),
                    item.get("expansion"),
                    item.get("exploration_path"),
                    item.get("score"),
                    item.get("status", "candidate"),
                    now,
                )
                for item in items
            ],
        )


def save_mobile_request(*, command: str, input_text: str, response_text: str | None) -> int:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO mobile_requests (command, input_text, response_text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (command, input_text, response_text, now),
        )
        return int(cursor.lastrowid)


def save_feedback(
    *,
    feedback_type: str,
    note: str,
    brief_id: int | None = None,
    item_id: int | None = None,
) -> int:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback (item_id, brief_id, feedback_type, note, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, brief_id, feedback_type, note, now),
        )
        return int(cursor.lastrowid)


def start_run(*, service: str, trigger_type: str) -> int:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO run_logs (service, trigger_type, status, started_at)
            VALUES (?, ?, ?, ?)
            """,
            (service, trigger_type, "running", now),
        )
        return int(cursor.lastrowid)


def finish_run(
    run_id: int,
    *,
    status: str,
    returncode: int | None = None,
    stdout: str | None = None,
    stderr: str | None = None,
    error: str | None = None,
) -> None:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        row = conn.execute("SELECT started_at FROM run_logs WHERE id = ?", (run_id,)).fetchone()
        duration_ms = None
        if row is not None:
            started_at = datetime.fromisoformat(row["started_at"])
            finished_at = datetime.fromisoformat(now)
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        conn.execute(
            """
            UPDATE run_logs
            SET
                status = ?,
                finished_at = ?,
                duration_ms = ?,
                returncode = ?,
                stdout = ?,
                stderr = ?,
                error = ?
            WHERE id = ?
            """,
            (status, now, duration_ms, returncode, stdout, stderr, error, run_id),
        )


def list_recent_runs(limit: int = 20) -> list[sqlite3.Row]:
    init_db()
    with connect() as conn:
        return conn.execute(
            """
            SELECT
                id,
                service,
                trigger_type,
                status,
                started_at,
                finished_at,
                duration_ms,
                returncode,
                stdout,
                stderr,
                error
            FROM run_logs
            ORDER BY started_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_latest_brief() -> sqlite3.Row | None:
    init_db()
    with connect() as conn:
        return conn.execute(
            """
            SELECT id, run_date, title, content, markdown_path, updated_at
            FROM briefs
            ORDER BY run_date DESC, updated_at DESC
            LIMIT 1
            """
        ).fetchone()


def get_items_for_brief(brief_id: int) -> list[sqlite3.Row]:
    init_db()
    with connect() as conn:
        return conn.execute(
            """
            SELECT
                id,
                brief_id,
                title,
                source,
                url,
                category,
                hook,
                why_now,
                why_fit,
                next_action,
                expansion,
                exploration_path,
                score,
                status,
                created_at
            FROM items
            WHERE brief_id = ?
            ORDER BY id
            """,
            (brief_id,),
        ).fetchall()


def list_recent_feedback(limit: int = 20) -> list[sqlite3.Row]:
    init_db()
    with connect() as conn:
        return conn.execute(
            """
            SELECT
                f.id,
                f.item_id,
                f.brief_id,
                f.feedback_type,
                f.note,
                f.created_at,
                b.run_date AS brief_date,
                i.title AS item_title
            FROM feedback f
            LEFT JOIN briefs b ON b.id = f.brief_id
            LEFT JOIN items i ON i.id = f.item_id
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def reveal_next_item(brief_id: int) -> sqlite3.Row | None:
    init_db()
    with connect() as conn:
        item = conn.execute(
            """
            SELECT
                id,
                brief_id,
                title,
                source,
                url,
                category,
                hook,
                why_now,
                why_fit,
                next_action,
                expansion,
                exploration_path,
                score,
                status,
                created_at
            FROM items
            WHERE brief_id = ? AND status = 'candidate'
            ORDER BY id
            LIMIT 1
            """,
            (brief_id,),
        ).fetchone()

        if item is None:
            return None

        conn.execute(
            """
            UPDATE items SET status = 'revealed' WHERE id = ?
            """,
            (item["id"],),
        )
        return item
