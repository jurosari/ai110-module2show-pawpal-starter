"""PawPal+ logic layer.

Backend classes for the PawPal+ pet-care planner. This is the "logic layer":
it holds the core domain objects (Owner, Pet, Task, Schedule) and their
behavior, independent of any UI.

Class structure follows diagrams/uml.mmd.
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
        self.scheduled_time = time

    def reschedule(self, new_time: str) -> None:
        """Move this task to a new time."""
        self.scheduled_time = new_time

    def mark_completed(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def set_priority(self, p: int) -> None:
        """Set this task's priority."""
        self.priority = p


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
        task.pet_id = self.id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet by id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's not-yet-completed tasks."""
        return [t for t in self.tasks if not t.completed]

    def update_info(self, info: dict) -> None:
        """Update this pet's attributes from a dict of fields."""
        for key, value in info.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class Owner:
    """A pet owner with availability, preferences, and one or more pets."""

    id: str
    name: str
    availability: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    schedule: "Schedule | None" = None

    def set_availability(self, days: list[str], times: list[str]) -> None:
        """Record the days/times this owner is free for tasks."""
        for day in days:
            self.availability[day] = list(times)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet from this owner by id."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def update_preferences(self, prefs: dict) -> None:
        """Merge new preference settings into this owner's preferences."""
        self.preferences.update(prefs)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_daily_plan(self, date: str) -> list[Task]:
        """Return the ordered list of tasks planned for the given date.

        Delegates to the owner's Schedule (the "brain"). Returns an empty
        plan if no schedule has been assigned.
        """
        if self.schedule is None:
            return []
        return self.schedule.generate_daily_plan(self, date)


@dataclass
class Schedule:
    """Arranges tasks into timeslots and builds daily plans for an owner.

    This is the "brain" of PawPal+: it retrieves tasks across an owner's
    pets, organizes them into timeslots, and produces an ordered daily plan.
    """

    days_of_week: list[str] = field(default_factory=list)
    timeslots: list[str] = field(default_factory=list)
    slots: dict = field(default_factory=dict)

    def add_task(self, task: Task, time: str) -> None:
        """Place a task into the schedule at the given time."""
        task.schedule(time)
        self.slots.setdefault(time, []).append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from the schedule by id."""
        for time, tasks in self.slots.items():
            self.slots[time] = [t for t in tasks if t.id != task_id]

    def edit_task(self, task_id: str, new_time: str) -> None:
        """Change the scheduled time of a task already in the schedule."""
        for time, tasks in list(self.slots.items()):
            for task in tasks:
                if task.id == task_id:
                    self.remove_task(task_id)
                    self.add_task(task, new_time)
                    return

    def find_available_slot(self, duration: int, prefs: dict) -> str:
        """Find an open timeslot fitting the duration and preferences.

        Prefers the owner's preferred slots first, then any remaining slot
        with no task already booked. Returns "" if nothing is free.
        """
        preferred = prefs.get("preferred_times", [])
        ordered = preferred + [t for t in self.timeslots if t not in preferred]
        for time in ordered:
            if not self.slots.get(time):
                return time
        return ""

    def generate_daily_plan(self, owner: Owner, date: str) -> list[Task]:
        """Build an ordered task plan for the owner on the given date.

        Gathers every pending task across the owner's pets and orders them by
        priority (highest first), then by scheduled time.
        """
        pending = [
            task
            for pet in owner.pets
            for task in pet.get_pending_tasks()
        ]
        return sorted(
            pending,
            key=lambda t: (-t.priority, t.scheduled_time),
        )
