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


def test_priority_plan_avoids_overlaps_and_preserves_source_tasks():
    owner = build_demo(DAY)
    original_times = [task.time for _, task in owner.get_all_tasks()]
    plan = Scheduler(owner).build_plan(DAY)
    assert [task.time for _, task, _ in plan["scheduled"]] == ["08:00", "08:10", "09:00"]
    assert [task.description for _, task, _ in plan["deferred"]] == ["Enrichment play"]
    assert [task.time for _, task in owner.get_all_tasks()] == original_times
    scheduled = [task for _, task, _ in plan["scheduled"]]
    assert all(a.ends_at <= b.starts_at for a, b in zip(scheduled, scheduled[1:]))


def test_plan_prioritizes_high_tasks_when_time_is_limited():
    low = Task("Play", DAY, "08:00", 30, "low")
    high = Task("Medication", DAY, "08:00", 30, "high")
    owner = Owner("Jordan", [Pet("Mochi", "cat", [low]), Pet("Biscuit", "dog", [high])], available_minutes=30)
    plan = Scheduler(owner).build_plan(DAY)
    assert plan["scheduled"][0][1].id == high.id
    assert plan["deferred"][0][1].id == low.id


def test_plan_includes_overdue_but_excludes_completed_and_future_tasks():
    tasks = [Task("Overdue", DAY - timedelta(days=1), "15:00"),
             Task("Future", DAY + timedelta(days=1), "08:00"),
             Task("Completed", DAY, "08:00", completed=True)]
    plan = Scheduler(Owner("Jordan", [Pet("Mochi", "cat", tasks)])).build_plan(DAY)
    assert len(plan["scheduled"]) == 1
    assert plan["scheduled"][0][1].time == "08:00"
    assert "Overdue" in plan["scheduled"][0][2]


def test_plan_clips_at_midnight_and_accepts_exact_window_fit():
    tasks = [Task("Fits", DAY, "23:30", 30, "high"), Task("Too long", DAY, "23:30", 31)]
    plan = Scheduler(Owner("Jordan", [Pet("Mochi", "cat", tasks)], "23:30", 120)).build_plan(DAY)
    assert len(plan["scheduled"]) == 1
    assert len(plan["deferred"]) == 1
    assert plan["scheduled"][0][1].ends_at == plan["end"]


def test_json_round_trip_preserves_ids_dates_completion_and_preferences(tmp_path):
    owner = build_demo(DAY)
    Scheduler(owner).mark_task_complete(owner.pets[0].tasks[1].id)
    path = tmp_path / "data.json"
    owner.save_to_json(path)
    restored = Owner.load_from_json(path)
    assert restored == owner
    assert restored is not owner
    assert Scheduler(restored).detect_conflicts(DAY) == Scheduler(owner).detect_conflicts(DAY)


@pytest.mark.parametrize("content", ['not json', '{}', '[]', '{"version": 7, "owner": {}}',
    '{"version": 1, "owner": {"name": "Jordan", "pets": [{"name": "M", "species": "cat", "tasks": [{"due_date": "bad"}]}]}}'])
def test_bad_backups_are_rejected(content):
    with pytest.raises(ValueError, match="Invalid PawPal backup"):
        Owner.from_json(content)


def test_json_rejects_duplicate_task_ids_across_pets():
    import json
    owner = build_demo(DAY)
    data = json.loads(owner.to_json())
    data["owner"]["pets"][1]["tasks"][0]["id"] = data["owner"]["pets"][0]["tasks"][0]["id"]
    with pytest.raises(ValueError):
        Owner.from_json(json.dumps(data))


def test_priority_sort_is_high_then_medium_then_low_across_pets():
    pairs = Scheduler(build_demo(DAY)).sort_by_priority(DAY)
    assert [task.priority for _, task in pairs] == ["high", "high", "medium", "low"]
    assert {pet.name for pet, _ in pairs} == {"Mochi", "Biscuit"}


def test_next_slot_uses_gap_and_skips_overlapping_busy_intervals():
    from datetime import datetime
    start = datetime(2026, 10, 20, 8)
    end = start + timedelta(hours=2)
    busy = [(start + timedelta(minutes=50), start + timedelta(minutes=70)),
            (start, start + timedelta(minutes=20)),
            (start + timedelta(minutes=10), start + timedelta(minutes=30))]
    assert Scheduler.next_available_slot(start, 20, busy, end) == start + timedelta(minutes=30)
    assert Scheduler.next_available_slot(start, 51, busy, end) is None


def test_unknown_and_completed_tasks_cannot_be_edited():
    owner = build_demo(DAY)
    scheduler = Scheduler(owner)
    with pytest.raises(ValueError, match="not found"):
        scheduler.mark_task_complete("missing")
    with pytest.raises(ValueError, match="not found"):
        scheduler.update_task("missing", time="09:00")
    task = owner.pets[0].tasks[0]
    scheduler.mark_task_complete(task.id)
    with pytest.raises(ValueError, match="read-only"):
        scheduler.update_task(task.id, time="09:00")


def test_duplicate_occurrences_are_rejected():
    from dataclasses import replace
    task = Task("Walk", DAY, "08:00")
    pet = Pet("Biscuit", "dog", [task])
    with pytest.raises(ValueError):
        pet.add_task(task)
    owner = Owner("Jordan", [pet])
    with pytest.raises(ValueError):
        owner.add_pet(Pet("Mochi", "cat", [replace(task)]))


@pytest.mark.parametrize("changes", [{"name": " "}, {"preferred_start": "9:00"},
    {"available_minutes": 0}, {"available_minutes": True}])
def test_owner_validation(changes):
    values = {"name": "Jordan"}
    values.update(changes)
    with pytest.raises(ValueError):
        Owner(**values)


def test_recurrence_date_overflow_does_not_partly_complete_task():
    task = Task("Care", date.max, "08:00", frequency="daily")
    with pytest.raises(OverflowError):
        task.mark_complete()
    assert not task.completed
