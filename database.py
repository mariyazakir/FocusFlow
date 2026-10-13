from __future__ import annotations

import sqlite3
import calendar
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

CATEGORIES = ["MCA", "Side Income", "BUD", "Personal"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["To do", "In progress", "Done"]


class TaskStore:
    """Small SQLite repository for FocusFlow tasks."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                due_date TEXT,
                estimated_minutes INTEGER NOT NULL DEFAULT 30,
                status TEXT NOT NULL DEFAULT 'To do',
                recurring TEXT NOT NULL DEFAULT 'Never',
                permanent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(tasks)")}
            if "permanent" not in columns:
                db.execute("ALTER TABLE tasks ADD COLUMN permanent INTEGER NOT NULL DEFAULT 0")
            db.execute("""CREATE TABLE IF NOT EXISTS permanent_task_history (
                task_id INTEGER NOT NULL,
                task_date TEXT NOT NULL,
                status TEXT NOT NULL,
                PRIMARY KEY (task_id, task_date)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )""")

    def get_setting(self, key: str) -> str | None:
        with self._connect() as db:
            row = db.execute("SELECT setting_value FROM app_settings WHERE setting_key=?", (key,)).fetchone()
            return str(row[0]) if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO app_settings(setting_key,setting_value) VALUES(?,?) "
                "ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value",
                (key, value),
            )

    def delete_setting(self, key: str) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM app_settings WHERE setting_key=?", (key,))

    def create(self, title: str, description: str, category: str, priority: str, due_date: str | None, estimated_minutes: int, status: str = "To do", recurring: str = "Never", permanent: bool = False) -> int:
        with self._connect() as db:
            cursor = db.execute("INSERT INTO tasks(title,description,category,priority,due_date,estimated_minutes,status,recurring,permanent) VALUES(?,?,?,?,?,?,?,?,?)", (title, description, category, priority, due_date, estimated_minutes, status, recurring, int(permanent)))
            if permanent:
                db.execute("UPDATE tasks SET recurring='Never' WHERE id=?", (cursor.lastrowid,))
            return int(cursor.lastrowid)

    def reset_permanent_tasks(self, today: date | None = None) -> int:
        """Start today's fresh checklist for permanent tasks, keeping a status history."""
        today = today or date.today()
        today_text = today.isoformat()
        reset_count = 0
        with self._connect() as db:
            due_tasks = db.execute(
                "SELECT id, due_date, status FROM tasks WHERE permanent=1 AND (due_date IS NULL OR due_date < ?)",
                (today_text,),
            ).fetchall()
            for task in due_tasks:
                if task["due_date"]:
                    db.execute(
                        "INSERT OR IGNORE INTO permanent_task_history(task_id,task_date,status) VALUES(?,?,?)",
                        (task["id"], task["due_date"], task["status"]),
                    )
                db.execute("UPDATE tasks SET due_date=?, status='To do' WHERE id=?", (today_text, task["id"]))
                reset_count += 1
        return reset_count

    def list_all(self) -> list[dict]:
        with self._connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM tasks ORDER BY CASE status WHEN 'To do' THEN 0 WHEN 'In progress' THEN 1 ELSE 2 END, due_date IS NULL, due_date, id DESC")]

    def update_status(self, task_id: int, status: str) -> None:
        with self._connect() as db:
            task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            db.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
            if status == "Done" and task and task["recurring"] != "Never":
                old_due = date.fromisoformat(task["due_date"]) if task["due_date"] else date.today()
                if task["recurring"] == "Daily":
                    next_due = old_due + timedelta(days=1)
                elif task["recurring"] == "Weekly":
                    next_due = old_due + timedelta(days=7)
                else:
                    month = old_due.month % 12 + 1
                    year = old_due.year + (old_due.month // 12)
                    next_due = date(year, month, min(old_due.day, calendar.monthrange(year, month)[1]))
                db.execute("INSERT INTO tasks(title,description,category,priority,due_date,estimated_minutes,status,recurring) VALUES(?,?,?,?,?,?,?,?)", (task["title"], task["description"], task["category"], task["priority"], next_due.isoformat(), task["estimated_minutes"], "To do", task["recurring"]))

    def update(self, task_id: int, title: str, description: str, category: str, priority: str, due_date: str | None, estimated_minutes: int, recurring: str | None = None, permanent: bool | None = None) -> None:
        with self._connect() as db:
            if recurring is None and permanent is None:
                db.execute("UPDATE tasks SET title=?,description=?,category=?,priority=?,due_date=?,estimated_minutes=? WHERE id=?", (title, description, category, priority, due_date, estimated_minutes, task_id))
            elif recurring is not None and permanent is not None:
                db.execute("UPDATE tasks SET title=?,description=?,category=?,priority=?,due_date=?,estimated_minutes=?,recurring=?,permanent=? WHERE id=?", (title, description, category, priority, due_date, estimated_minutes, recurring, int(permanent), task_id))
            elif recurring is not None:
                db.execute("UPDATE tasks SET title=?,description=?,category=?,priority=?,due_date=?,estimated_minutes=?,recurring=? WHERE id=?", (title, description, category, priority, due_date, estimated_minutes, recurring, task_id))
            else:
                db.execute("UPDATE tasks SET title=?,description=?,category=?,priority=?,due_date=?,estimated_minutes=?,permanent=?,recurring=CASE WHEN ?=1 THEN 'Never' ELSE recurring END WHERE id=?", (title, description, category, priority, due_date, estimated_minutes, int(permanent), int(permanent), task_id))

    def update_due_date(self, task_id: int, due_date: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE tasks SET due_date=? WHERE id=?", (due_date, task_id))

    def delete(self, task_id: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
