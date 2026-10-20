"""Pet care domain objects and scheduling rules, independent of Streamlit."""
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta
from uuid import uuid4
import re
import json
from pathlib import Path

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
        if self.frequency == "once":
            self.completed = True
            return None
        intervals = {"daily": 1, "weekly": 7}
        if self.frequency not in intervals:
            raise ValueError(f"Unsupported frequency: {self.frequency!r}")
        # Prepare the successor before mutating history: failures leave it incomplete.
        following = replace(self, due_date=self.due_date + timedelta(days=intervals[self.frequency]),
                            id=uuid4().hex, completed=False)
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


    def to_json(self):
        """Serialize a versioned backup, including IDs, dates, and preferences."""
        return json.dumps({"version": 1, "owner": asdict(self)},
                          default=lambda value: value.isoformat(), indent=2)

    @classmethod
    def from_json(cls, content):
        """Validate an entire backup before returning a replacement owner."""
        try:
            data = json.loads(content)
            if data["version"] != 1:
                raise ValueError("Unsupported backup version.")
            values = dict(data["owner"])
            pets = []
            for raw_pet in values.pop("pets"):
                raw_pet = dict(raw_pet)
                tasks = []
                for raw_task in raw_pet.pop("tasks"):
                    raw_task = dict(raw_task)
                    raw_task["due_date"] = date.fromisoformat(raw_task["due_date"])
                    tasks.append(Task(**raw_task))
                pets.append(Pet(**raw_pet, tasks=tasks))
            return cls(**values, pets=pets)
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
            raise ValueError("Invalid PawPal backup. Use an unmodified version 1 JSON export.") from error

    def save_to_json(self, path):
        """Save a backup atomically so interrupted writes preserve the old file."""
        path = Path(path)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(self.to_json(), encoding="utf-8")
        temporary.replace(path)

    @classmethod
    def load_from_json(cls, path):
        """Restore saved pets and tasks without depending on Streamlit."""
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


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

    @staticmethod
    def next_available_slot(start, duration_minutes, busy, end):
        """Find the first fitting gap in sorted, half-open time intervals."""
        candidate = start
        duration = timedelta(minutes=duration_minutes)
        for occupied_start, occupied_end in sorted(busy):
            if candidate + duration <= occupied_start:
                break
            if candidate < occupied_end:
                candidate = occupied_end
        return candidate if candidate + duration <= end else None

    def build_plan(self, day):
        """Greedily time-block pending due/overdue tasks by priority, then time."""
        start = datetime.combine(day, datetime.strptime(self.owner.preferred_start, "%H:%M").time())
        midnight = datetime.combine(day + timedelta(days=1), datetime.min.time())
        end = min(start + timedelta(minutes=self.owner.available_minutes), midnight)
        candidates = [(pet, task) for pet, task in self.owner.get_all_tasks()
                      if not task.completed and task.due_date <= day]
        candidates.sort(key=lambda pair: (PRIORITIES[pair[1].priority], pair[1].starts_at))
        busy, scheduled, deferred = [], [], []
        for pet, task in candidates:
            earliest = max(start, task.starts_at) if task.due_date == day else start
            slot = self.next_available_slot(earliest, task.duration_minutes, busy, end)
            if slot is None:
                deferred.append((pet, task, "No remaining slot in the care window."))
                continue
            planned = replace(task, due_date=day, time=slot.strftime("%H:%M"))
            busy.append((slot, planned.ends_at))
            reason = f"{task.priority.capitalize()} priority; earliest available slot at or after the requested time."
            if task.due_date < day:
                reason = f"Overdue from {task.due_date}; {reason[0].lower() + reason[1:]}"
            scheduled.append((pet, planned, reason))
        scheduled.sort(key=lambda item: item[1].starts_at)
        return {"scheduled": scheduled, "deferred": deferred, "start": start, "end": end}
