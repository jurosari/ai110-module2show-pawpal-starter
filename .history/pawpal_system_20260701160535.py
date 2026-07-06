"""PawPal+ logic layer.

Backend classes for the PawPal+ pet-care planner. This is the "logic layer":
it holds the core domain objects (Owner, Pet, Task, Schedule) and their
behavior, independent of any UI.

Class structure follows diagrams/uml.mmd.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

# How far each recurrence frequency advances the due date. "once" (or any
# value not listed here) means the task does not repeat.
FREQUENCY_DELTAS: dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),  # weeks=1 == days=7, but reads clearer
}


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
    frequency: str = "once"      # "once" | "daily" | "weekly"
    due_date: str = ""           # ISO "YYYY-MM-DD"; "" means undated

    def is_recurring(self) -> bool:
        """True if this task repeats (daily/weekly), False for one-offs."""
        return self.frequency in FREQUENCY_DELTAS

    def next_occurrence(self) -> "Task | None":
        """Return a fresh, uncompleted copy scheduled for the next date.

        For a "daily" task the new due date is this task's due date + 1 day;
        for "weekly" it is + 7 days. timedelta does this arithmetic safely,
        rolling over month/year boundaries for us. If the task has no due
        date yet, we base the next occurrence on today. One-off tasks return
        None (nothing to repeat).
        """
        delta = FREQUENCY_DELTAS.get(self.frequency)
        if delta is None:
            return None

        base = date.fromisoformat(self.due_date) if self.due_date else date.today()
        next_date = (base + delta).isoformat()

        return Task(
            id=f"{self.id}@{next_date}",
            pet_id=self.pet_id,
            type=self.type,
            scheduled_time=self.scheduled_time,
            duration_minutes=self.duration_minutes,
            completed=False,
            priority=self.priority,
            frequency=self.frequency,
            due_date=next_date,
        )

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

    def complete_task(self, task_id: str) -> Task | None:
        """Mark a task complete and, if it recurs, queue its next occurrence.

        Marking a "daily"/"weekly" task done spawns a fresh, uncompleted copy
        for the next date and appends it to this pet's task list. Returns the
        newly created follow-up task, or None for one-off tasks / unknown ids.
        """
        for task in self.tasks:
            if task.id == task_id:
                task.mark_completed()
                follow_up = task.next_occurrence()
                if follow_up is not None:
                    self.tasks.append(follow_up)
                return follow_up
        return None

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

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return a new list of tasks ordered chronologically by their time.

        Uses sorted() with a lambda "key". Because scheduled_time is a
        zero-padded 24-hour "HH:MM" string ("08:00", "12:00", "18:00"),
        plain string comparison already matches clock order — so the key
        just returns t.scheduled_time. Untimed tasks (empty string) are
        pushed to the end with a "99:99" sentinel instead of the front.
        """
        return sorted(tasks, key=lambda t: t.scheduled_time or "99:99")

    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        completed: bool | None = None,
        pet_id: str | None = None,
    ) -> list[Task]:
        """Return the tasks matching the given completion status and/or pet.

        Each filter is optional. Passing only ``completed=False`` returns
        pending tasks; passing only ``pet_id`` returns one pet's tasks;
        passing both narrows on both. With no filters, returns all tasks.
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_id is not None:
            result = [t for t in result if t.pet_id == pet_id]
        return result

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
