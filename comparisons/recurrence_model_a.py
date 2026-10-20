"""GPT-6 Sol response to the recurrence comparison prompt."""
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4


def complete_recurring(task):
    if task.completed:
        return None

    if task.frequency == "once":
        task.completed = True
        return None

    days = {"daily": 1, "weekly": 7}.get(task.frequency)
    if days is None:
        raise ValueError(f"Unsupported frequency: {task.frequency!r}")

    next_date = task.due_date + timedelta(days=days)
    next_occurrence = replace(
        task,
        id=uuid4().hex,
        due_date=next_date,
        completed=False,
    )
    task.completed = True
    return next_occurrence
