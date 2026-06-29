"""PawPal+ logic layer.

Backend classes for the PawPal+ pet-care planner. This is the "logic layer":
it holds the core domain objects (Owner, Pet, Task, Schedule) and their
behavior, independent of any UI.

Class skeleton generated from diagrams/uml.mmd. Method bodies are stubs to be
filled in.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single care activity for a pet (e.g. walk, feed, medication)."""

    id: str
    pet_id: str
    type: str
    scheduled_time: str = ""
    duration_minutes: int = 0
    completed: bool = False
    priority: int = 0

    def schedule(self, time: str) -> None:
        """Assign a scheduled time to this task."""
        raise NotImplementedError

    def reschedule(self, new_time: str) -> None:
        """Move this task to a new time."""
        raise NotImplementedError

    def mark_completed(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def set_priority(self, p: int) -> None:
        """Set this task's priority."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet owned by an Owner, with its own list of care tasks."""

    id: str
    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        raise NotImplementedError

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet by id."""
        raise NotImplementedError

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's not-yet-completed tasks."""
        raise NotImplementedError

    def update_info(self, info: dict) -> None:
        """Update this pet's attributes from a dict of fields."""
        raise NotImplementedError


@dataclass
class Owner:
    """A pet owner with availability, preferences, and one or more pets."""

    id: str
    name: str
    availability: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def set_availability(self, days: list[str], times: list[str]) -> None:
        """Record the days/times this owner is free for tasks."""
        raise NotImplementedError

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet from this owner by id."""
        raise NotImplementedError

    def update_preferences(self, prefs: dict) -> None:
        """Merge new preference settings into this owner's preferences."""
        raise NotImplementedError

    def get_daily_plan(self, date: str) -> list[Task]:
        """Return the ordered list of tasks planned for the given date."""
        raise NotImplementedError


@dataclass
class Schedule:
    """Arranges tasks into timeslots and builds daily plans for an owner."""

    days_of_week: list[str] = field(default_factory=list)
    timeslots: list[str] = field(default_factory=list)
    slots: dict = field(default_factory=dict)

    def add_task(self, task: Task, time: str) -> None:
        """Place a task into the schedule at the given time."""
        raise NotImplementedError

    def remove_task(self, task_id: str) -> None:
        """Remove a task from the schedule by id."""
        raise NotImplementedError

    def edit_task(self, task_id: str, new_time: str) -> None:
        """Change the scheduled time of a task already in the schedule."""
        raise NotImplementedError

    def find_available_slot(self, duration: int, prefs: dict) -> str:
        """Find an open timeslot fitting the duration and preferences."""
        raise NotImplementedError

    def generate_daily_plan(self, owner: Owner, date: str) -> list[Task]:
        """Build an ordered task plan for the owner on the given date."""
        raise NotImplementedError
