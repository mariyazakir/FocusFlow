"""Free, offline helpers used by FocusFlow's planning page."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta


PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def build_day_plan(tasks: list[dict], plan_date: date, capacity_minutes: int, start_at: time = time(9, 0), break_minutes: int = 10) -> list[dict]:
    """Rank active work, then fit it into a single day's available focus time."""
    active = [task for task in tasks if task.get("status") != "Done"]
    active.sort(key=lambda task: (
        PRIORITY_ORDER.get(task.get("priority", "Medium"), 1),
        task.get("due_date") or "9999-12-31",
        task.get("estimated_minutes", 30),
        task.get("id", 0),
    ))

    planned: list[dict] = []
    remaining = max(0, capacity_minutes)
    cursor = datetime.combine(plan_date, start_at)
    for task in active:
        duration = max(5, int(task.get("estimated_minutes", 30)))
        if duration > remaining:
            continue
        end = cursor + timedelta(minutes=duration)
        planned.append({"task": task, "start": cursor.time(), "end": end.time(), "minutes": duration})
        remaining -= duration
        cursor = end + timedelta(minutes=break_minutes)
    return planned


def breakdown_for(task: dict) -> list[str]:
    """Create practical, local-only starter steps; no AI service or API is used."""
    title = task.get("title", "your task").strip().rstrip(".?!") or "your task"
    category = task.get("category", "Personal")
    if category == "MCA":
        steps = ["Read the prompt and note the requirements", "Gather class notes and reference material", "Complete the main work in focused sections", "Review against the rubric and submit"]
    elif category == "Side Income":
        steps = ["Define the outcome and who it is for", "Prepare the materials or tools you need", "Complete the highest-value part first", "Check the result and record the next action"]
    elif category == "BUD":
        steps = ["Write down the smallest useful outcome", "Sketch the approach before building", "Build and check one small piece at a time", "Review what works and note the next improvement"]
    else:
        steps = ["Decide what finished looks like", "Gather what you need and clear a little space", "Work through the task in a few small steps", "Check it off and prepare anything needed next"]
    return [f"{step} — {title}" for step in steps]
