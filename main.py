"""Run a reproducible multi-pet demonstration without starting the UI."""
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo(day=None):
    """Create two pets with intentionally unsorted and conflicting tasks."""
    day = day or date(2026, 10, 20)
    owner = Owner("Jordan")
    mochi, biscuit = Pet("Mochi", "cat"), Pet("Biscuit", "dog")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)
    mochi.add_task(Task("Enrichment play", day, "10:00", 25, "low"))
    mochi.add_task(Task("Breakfast", day, "08:00", 10, "high", "daily"))
    biscuit.add_task(Task("Morning walk", day, "08:00", 30, "high", "daily"))
    biscuit.add_task(Task("Grooming", day, "09:00", 20, "medium", "weekly"))
    return owner


def print_schedule(title, pairs):
    """Print an aligned table that is readable in a plain terminal."""
    print(f"\n{title}")
    print(f"{'Time':<7} {'Pet':<10} {'Task':<24} {'Mins':>4}  {'Priority':<8} Status")
    print("-" * 74)
    for pet, task in pairs:
        print(f"{task.time:<7} {pet.name:<10} {task.description:<24} {task.duration_minutes:>4}  "
              f"{task.priority:<8} {'Done' if task.completed else 'Pending'}")


def main():
    """Demonstrate sorting, filtering, conflicts, and idempotent recurrence."""
    day = date(2026, 10, 20)
    owner = build_demo(day)
    scheduler = Scheduler(owner)
    print(f"PawPal+ | {owner.name} | {day.isoformat()}")
    print_schedule("Today's Schedule", scheduler.sort_by_time(day))
    print_schedule("Priority order | high, medium, low; then due time", scheduler.sort_by_priority(day))
    print_schedule("Biscuit's pending tasks", scheduler.sort_by_time(day, "Biscuit", False))
    for warning in scheduler.detect_conflicts(day):
        print(f"WARNING: {warning}")
    plan = scheduler.build_plan(day)
    print_schedule("Priority plan | 08:00–10:00 | no overlapping care", [(pet, task) for pet, task, _ in plan["scheduled"]])
    for pet, task, reason in plan["deferred"]:
        print(f"DEFERRED: {pet.name}: {task.description}. {reason}")
    breakfast = next(task for _, task in owner.get_all_tasks() if task.description == "Breakfast")
    following = scheduler.mark_task_complete(breakfast.id)
    print(f"\nCompleted Breakfast; next daily occurrence: {following.due_date} {following.time}.")


if __name__ == "__main__":
    main()
