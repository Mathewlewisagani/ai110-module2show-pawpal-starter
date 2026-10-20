"""Pet care domain objects and scheduling rules, independent of Streamlit."""
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from uuid import uuid4
import re

PRIORITIES = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once": 0, "daily": 1, "weekly": 7}


def _text(value, label):
    """Require nonempty, trimmed text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must not be empty.")
    return value.strip()


@dataclass
class Task:
    """One dated care occurrence; recurring completion returns a new occurrence."""
    description: str
    due_date: date
    time: str
    duration_minutes: int = 20
    priority: str = "medium"
    frequency: str = "once"
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self):
        """Validate task inputs at the domain boundary."""
        self.description = _text(self.description, "Task description")
        if type(self.due_date) is not date:
            raise ValueError("Due date must be a date.")
        if not isinstance(self.time, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", self.time):
            raise ValueError("Time must use 24-hour HH:MM format.")
        if type(self.duration_minutes) is not int or not 1 <= self.duration_minutes <= 1440:
            raise ValueError("Duration must be between 1 and 1440 whole minutes.")
        if self.priority not in PRIORITIES:
            raise ValueError("Priority must be high, medium, or low.")
        if self.frequency not in FREQUENCIES:
            raise ValueError("Frequency must be once, daily, or weekly.")
        if type(self.completed) is not bool:
            raise ValueError("Completion status must be true or false.")
        self.id = _text(self.id, "Task ID")

    @property
    def starts_at(self):
        """Combine the local due date and time into one sortable value."""
        return datetime.combine(self.due_date, datetime.strptime(self.time, "%H:%M").time())

    @property
    def ends_at(self):
        """Return the exclusive end of the task's occupied time block."""
        return self.starts_at + timedelta(minutes=self.duration_minutes)

    def mark_complete(self):
        """Complete once and return the next recurrence, anchored to its due date."""
        if self.completed:
            return None
        days = FREQUENCIES[self.frequency]
        # Construct first so an unrepresentable next date cannot partly complete a task.
        following = replace(self, due_date=self.due_date + timedelta(days=days), id=uuid4().hex) if days else None
        self.completed = True
        return following


@dataclass
class Pet:
    """A named pet and its care history."""
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self):
        """Validate identification and existing tasks."""
        self.name = _text(self.name, "Pet name")
        self.species = _text(self.species, "Species")
        tasks, self.tasks = self.tasks, []
        for task in tasks:
            self.add_task(task)

    def add_task(self, task):
        """Add a task while rejecting duplicate occurrence IDs."""
        if not isinstance(task, Task):
            raise ValueError("A pet's tasks must be Task objects.")
        if any(existing.id == task.id for existing in self.tasks):
            raise ValueError("This task is already attached to the pet.")
        self.tasks.append(task)

    def list_tasks(self):
        """Return a copy of the pet's task collection."""
        return list(self.tasks)


@dataclass
class Owner:
    """One caregiver whose pets share time and planning preferences."""
    name: str
    pets: list[Pet] = field(default_factory=list)
    preferred_start: str = "08:00"
    available_minutes: int = 120

    def __post_init__(self):
        """Validate owner information and register the initial pets."""
        self.name = _text(self.name, "Owner name")
        # Reuse task time validation instead of maintaining a second parser.
        Task("Preference validation", date.today(), self.preferred_start)
        if type(self.available_minutes) is not int or not 1 <= self.available_minutes <= 1440:
            raise ValueError("Available minutes must be between 1 and 1440.")
        pets, self.pets = self.pets, []
        for pet in pets:
            self.add_pet(pet)

    def add_pet(self, pet):
        """Register a pet with a unique name and unique task IDs."""
        if not isinstance(pet, Pet):
            raise ValueError("Owner pets must be Pet objects.")
        if any(existing.name.casefold() == pet.name.casefold() for existing in self.pets):
            raise ValueError("A pet with this name already exists.")
        known_ids = {task.id for _, task in self.get_all_tasks()}
        if any(task.id in known_ids for task in pet.tasks):
            raise ValueError("Task IDs must be unique across pets.")
        self.pets.append(pet)

    def get_all_tasks(self):
        """Return (pet, task) pairs across every registered pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Organize one owner's complete collection of care tasks."""
    owner: Owner

    def filter_tasks(self, pet_name=None, completed=None, day=None):
        """Select across all pets using optional name, completion, and due date."""
        return [(pet, task) for pet, task in self.owner.get_all_tasks()
                if (pet_name is None or pet.name.casefold() == pet_name.casefold())
                and (completed is None or task.completed == completed)
                and (day is None or task.due_date == day)]

    def sort_by_time(self, day=None, pet_name=None, completed=None):
        """Return chronological task pairs without changing the stored order."""
        return sorted(self.filter_tasks(pet_name, completed, day), key=lambda pair: pair[1].starts_at)

    def sort_by_priority(self, day=None):
        """Rank pending tasks by high/medium/low priority, then due time."""
        return sorted(self.filter_tasks(completed=False, day=day),
                      key=lambda pair: (PRIORITIES[pair[1].priority], pair[1].starts_at))

    def mark_task_complete(self, task_id):
        """Complete the identified task and attach its next occurrence to its pet."""
        for pet, task in self.owner.get_all_tasks():
            if task.id == task_id:
                following = task.mark_complete()
                if following:
                    pet.add_task(following)
                return following
        raise ValueError("Task not found.")

    def update_task(self, task_id, **changes):
        """Validate and replace a task atomically while keeping its identity."""
        allowed = {"description", "due_date", "time", "duration_minutes", "priority", "frequency"}
        if not changes.keys() <= allowed:
            raise ValueError("Only task details can be edited.")
        for pet, task in self.owner.get_all_tasks():
            if task.id == task_id:
                if task.completed:
                    raise ValueError("Completed occurrences are read-only.")
                updated = replace(task, **changes)
                pet.tasks[pet.tasks.index(task)] = updated
                return updated
        raise ValueError("Task not found.")

    def detect_conflicts(self, day=None):
        """Warn about overlapping pending tasks, including midnight spillovers."""
        pairs = self.sort_by_time(completed=False)
        warnings = []
        for index, (pet, task) in enumerate(pairs):
            for other_pet, other in pairs[index + 1:]:
                if other.starts_at >= task.ends_at:
                    break
                if day is not None:
                    start = datetime.combine(day, datetime.min.time())
                    end = start + timedelta(days=1)
                    if not (max(task.starts_at, other.starts_at, start) < min(task.ends_at, other.ends_at, end)):
                        continue
                warnings.append(f"{task.due_date.isoformat()} {task.time} {pet.name}: {task.description} overlaps "
                                f"{other.due_date.isoformat()} {other.time} {other_pet.name}: {other.description}.")
        return warnings
