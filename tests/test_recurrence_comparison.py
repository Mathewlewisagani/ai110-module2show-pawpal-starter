"""Apply identical behavioral checks to both independent model responses."""
from datetime import date, timedelta
import pytest
from comparisons.recurrence_model_a import complete_recurring as model_a
from comparisons.recurrence_model_b import complete_recurring as model_b
from pawpal_system import Task


@pytest.fixture(params=[model_a, model_b], ids=["gpt-6-sol", "gpt-6.1-sol"])
def complete(request):
    return request.param


@pytest.mark.parametrize("frequency,days", [("daily", 1), ("weekly", 7)])
def test_due_date_anchoring_metadata_and_duplicate_completion(complete, frequency, days):
    task = Task("Care", date(2026, 12, 31), "08:15", 35, "high", frequency)
    following = complete(task)
    assert task.completed
    assert following.due_date == date(2026, 12, 31) + timedelta(days=days)
    assert following.id != task.id
    assert not following.completed
    assert (following.description, following.time, following.duration_minutes, following.priority, following.frequency) == (
        task.description, task.time, task.duration_minutes, task.priority, task.frequency)
    assert complete(task) is None


def test_one_time_completion(complete):
    task = Task("Walk", date(2026, 10, 20), "08:00")
    assert complete(task) is None
    assert task.completed
    assert complete(task) is None


def test_leap_day(complete):
    task = Task("Care", date(2028, 2, 28), "08:00", frequency="daily")
    assert complete(task).due_date == date(2028, 2, 29)


def test_overflow_leaves_original_incomplete(complete):
    task = Task("Care", date.max, "08:00", frequency="weekly")
    with pytest.raises(OverflowError):
        complete(task)
    assert not task.completed


def test_invalid_frequency_leaves_original_incomplete(complete):
    task = Task("Care", date(2026, 10, 20), "08:00")
    task.frequency = "monthly"
    with pytest.raises(ValueError):
        complete(task)
    assert not task.completed
