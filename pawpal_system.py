"""PawPal's interface-first design; implementation follows in the next increment."""
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    description: str
    due_date: date
    time: str
    duration_minutes: int = 20
    priority: str = "medium"
    frequency: str = "once"
    completed: bool = False

    def mark_complete(self):
        """Complete this occurrence."""
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task):
        """Attach a care task to this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet):
        """Register a pet with the owner."""
        raise NotImplementedError

    def get_all_tasks(self):
        """Return tasks across every pet."""
        raise NotImplementedError


@dataclass
class Scheduler:
    owner: Owner

    def sort_by_time(self, day=None):
        """Return tasks in chronological order across all pets."""
        raise NotImplementedError

    def filter_tasks(self, pet_name=None, completed=None, day=None):
        """Select tasks by pet, completion status, or date."""
        raise NotImplementedError

    def detect_conflicts(self, day=None):
        """Identify competing care tasks."""
        raise NotImplementedError
