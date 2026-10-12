import unittest
from datetime import date, time

from planner import breakdown_for, build_day_plan


class PlannerTests(unittest.TestCase):
    def test_day_plan_prioritizes_urgent_high_priority_tasks_and_respects_capacity(self):
        tasks = [
            {"id": 1, "title": "Later", "status": "To do", "priority": "Low", "due_date": "2026-10-25", "estimated_minutes": 45},
            {"id": 2, "title": "Urgent", "status": "To do", "priority": "High", "due_date": "2026-10-13", "estimated_minutes": 30},
            {"id": 3, "title": "Done", "status": "Done", "priority": "High", "due_date": "2026-10-12", "estimated_minutes": 15},
        ]
        plan = build_day_plan(tasks, date(2026, 10, 12), 60, time(9, 0), 5)
        self.assertEqual([item["task"]["title"] for item in plan], ["Urgent"])
        self.assertEqual(plan[0]["end"], time(9, 30))

    def test_breakdown_has_four_category_specific_steps(self):
        steps = breakdown_for({"title": "Build a feature", "category": "BUD"})
        self.assertEqual(len(steps), 4)
        self.assertTrue(all("Build a feature" in step for step in steps))


if __name__ == "__main__":
    unittest.main()
