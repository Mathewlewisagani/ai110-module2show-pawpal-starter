"""GPT-6.1 Sol response to the recurrence comparison prompt."""
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4


def complete_recurring(task):
    if task.completed:
        return None

    if task.frequency == "once":
        task.completed = True
        return None

    intervals = {"daily": 1, "weekly": 7}
    if task.frequency not in intervals:
        raise ValueError(f"Unsupported frequency: {task.frequency!r}")

    # Construct the successor before changing the original.
    next_due_date = task.due_date + timedelta(
        days=intervals[task.frequency]
    )
    next_task = replace(
        task,
        id=uuid4().hex,
        due_date=next_due_date,
        completed=False,
    )
    task.completed = True
    return next_task
