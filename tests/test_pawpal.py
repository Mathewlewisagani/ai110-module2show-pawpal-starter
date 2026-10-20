"""Behavioral checks for the shared multi-pet scheduling domain."""
from datetime import date, timedelta
import pytest
from pawpal_system import Owner, Pet, Scheduler, Task
from main import build_demo

DAY = date(2026, 10, 20)


def test_completion_and_pet_addition():
    pet = Pet("Mochi", "cat")
    task = Task("Breakfast", DAY, "08:00")
    pet.add_task(task)
    assert pet.list_tasks() == [task]
    assert task.mark_complete() is None
    assert task.completed


def test_chronological_sort_across_pets_without_mutating_storage():
    owner = build_demo(DAY)
    original = owner.pets[0].list_tasks()
    pairs = Scheduler(owner).sort_by_time(DAY)
    assert [task.time for _, task in pairs] == ["08:00", "08:00", "09:00", "10:00"]
    assert {pet.name for pet, _ in pairs} == {"Mochi", "Biscuit"}
    assert owner.pets[0].tasks == original


@pytest.mark.parametrize("frequency,days", [("daily", 1), ("weekly", 7)])
def test_recurrence_is_one_new_occurrence_and_completion_is_idempotent(frequency, days):
    task = Task("Care", date(2026, 12, 31), "08:00", frequency=frequency)
    pet = Pet("Mochi", "cat", [task])
    scheduler = Scheduler(Owner("Jordan", [pet]))
    following = scheduler.mark_task_complete(task.id)
    assert following.due_date == task.due_date + timedelta(days=days)
    assert following.id != task.id
    assert not following.completed
    assert scheduler.mark_task_complete(task.id) is None
    assert len(pet.tasks) == 2


def test_filters_combine_pet_status_and_date():
    owner = build_demo(DAY)
    scheduler = Scheduler(owner)
    task = owner.pets[1].tasks[0]
    scheduler.mark_task_complete(task.id)
    assert scheduler.filter_tasks("bISCUIT", True, DAY) == [(owner.pets[1], task)]
    assert scheduler.filter_tasks("Missing") == []
    assert scheduler.filter_tasks(day=DAY + timedelta(days=2)) == []


def test_conflicts_cross_pets_and_exact_time_matches():
    scheduler = Scheduler(build_demo(DAY))
    warnings = scheduler.detect_conflicts(DAY)
    assert len(warnings) == 1
    assert "Mochi" in warnings[0] and "Biscuit" in warnings[0]


def test_adjacent_and_completed_tasks_are_not_conflicts():
    tasks = [Task("First", DAY, "08:00", 30), Task("Adjacent", DAY, "08:30", 10),
             Task("Done", DAY, "08:00", completed=True)]
    assert Scheduler(Owner("Jordan", [Pet("Mochi", "cat", tasks)])).detect_conflicts() == []


def test_conflict_across_midnight_and_different_dates():
    tasks = [Task("Late", DAY, "23:50", 30), Task("Early", DAY + timedelta(days=1), "00:05", 10),
             Task("Another day", DAY + timedelta(days=2), "00:05", 10)]
    scheduler = Scheduler(Owner("Jordan", [Pet("Mochi", "cat", tasks)]))
    assert len(scheduler.detect_conflicts(DAY + timedelta(days=1))) == 1
    assert scheduler.detect_conflicts(DAY) == []
    assert scheduler.detect_conflicts(DAY + timedelta(days=2)) == []


def test_edits_are_validated_atomically():
    owner = build_demo(DAY)
    scheduler = Scheduler(owner)
    original = owner.pets[0].tasks[0]
    with pytest.raises(ValueError):
        scheduler.update_task(original.id, time="25:00")
    assert owner.pets[0].tasks[0] is original
    updated = scheduler.update_task(original.id, description="Quiet play", priority="high")
    assert updated.id == original.id
    assert updated.description == "Quiet play"


@pytest.mark.parametrize("changes", [{"time": "8:00"}, {"time": "24:00"}, {"description": "  "},
    {"duration_minutes": 0}, {"duration_minutes": True}, {"priority": "urgent"}, {"frequency": "monthly"}])
def test_invalid_task_inputs(changes):
    values = dict(description="Walk", due_date=DAY, time="08:00")
    values.update(changes)
    with pytest.raises(ValueError):
        Task(**values)


def test_empty_owner_and_duplicate_pet_names():
    owner = Owner("Jordan")
    assert Scheduler(owner).sort_by_time() == []
    assert Scheduler(owner).detect_conflicts() == []
    owner.add_pet(Pet("Mochi", "cat"))
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "cat"))
