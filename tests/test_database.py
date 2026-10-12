import unittest
from pathlib import Path
from uuid import uuid4
from datetime import date, timedelta

from database import TaskStore


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.db_path = Path(__file__).parent / f"test-{uuid4().hex}.db"
        self.store = TaskStore(self.db_path)

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    def test_create_and_list_task(self):
        task_id = self.store.create("Read chapter", "Take notes", "MCA", "High", "2026-10-20", 40)
        task = self.store.list_all()[0]
        self.assertEqual(task["id"], task_id)
        self.assertEqual(task["title"], "Read chapter")
        self.assertEqual(task["status"], "To do")

    def test_update_and_delete_task(self):
        task_id = self.store.create("Draft", "", "BUD", "Low", None, 30)
        self.store.update(task_id, "Publish draft", "Review first", "BUD", "High", "2026-10-22", 60)
        self.store.update_status(task_id, "In progress")
        task = self.store.list_all()[0]
        self.assertEqual(task["title"], "Publish draft")
        self.assertEqual(task["status"], "In progress")
        self.store.delete(task_id)
        self.assertEqual(self.store.list_all(), [])

    def test_completing_recurring_task_creates_next_occurrence(self):
        task_id = self.store.create("Weekly review", "", "Personal", "Medium", "2026-10-20", 30, recurring="Weekly")
        self.store.update_status(task_id, "Done")
        tasks = self.store.list_all()
        self.assertEqual(len(tasks), 2)
        next_task = next(task for task in tasks if task["status"] == "To do")
        self.assertEqual(next_task["due_date"], "2026-10-27")

    def test_due_date_can_be_moved_to_carry_over_day(self):
        task_id = self.store.create("Unfinished", "", "MCA", "High", "2026-10-10", 30)
        self.store.update_due_date(task_id, "2026-10-12")
        self.assertEqual(self.store.list_all()[0]["due_date"], "2026-10-12")

    def test_permanent_task_resets_for_new_day_and_keeps_history(self):
        yesterday = date(2026, 10, 11)
        today = yesterday + timedelta(days=1)
        task_id = self.store.create("Morning review", "", "Personal", "Low", yesterday.isoformat(), 10, permanent=True)
        self.store.update_status(task_id, "Done")

        self.assertEqual(self.store.reset_permanent_tasks(today), 1)
        task = self.store.list_all()[0]
        self.assertEqual(task["due_date"], today.isoformat())
        self.assertEqual(task["status"], "To do")
        self.assertEqual(self.store.reset_permanent_tasks(today), 0)

        with self.store._connect() as db:
            history = db.execute("SELECT task_date,status FROM permanent_task_history WHERE task_id=?", (task_id,)).fetchone()
        self.assertEqual(tuple(history), (yesterday.isoformat(), "Done"))

    def test_non_permanent_tasks_do_not_reset(self):
        yesterday = date(2026, 10, 11)
        today = yesterday + timedelta(days=1)
        task_id = self.store.create("Assignment", "", "MCA", "High", yesterday.isoformat(), 30)
        self.store.update_status(task_id, "In progress")
        self.assertEqual(self.store.reset_permanent_tasks(today), 0)
        task = self.store.list_all()[0]
        self.assertEqual(task["due_date"], yesterday.isoformat())
        self.assertEqual(task["status"], "In progress")

    def test_app_settings_store_consent_version(self):
        self.store.set_setting("legal_accepted_version", "2026-10-12-v1")
        self.assertEqual(self.store.get_setting("legal_accepted_version"), "2026-10-12-v1")
        self.assertIsNone(self.store.get_setting("unknown_setting"))


if __name__ == "__main__":
    unittest.main()
