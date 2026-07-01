"""Tests for the PawPal+ logic layer (pawpal_system.py).

Covers the three required behaviors — sorting, recurrence, conflict
detection — plus the edge cases surfaced during review (empty pets,
untimed tasks, one-off completion).

Run from the project root with:  pytest -v
"""

from datetime import date, timedelta

# Make the project root importable when pytest runs from inside tests/.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Schedule, Task  # noqa: E402


# --------------------------------------------------------------------------- #
# Small helpers so each test reads clearly instead of repeating constructors.
# --------------------------------------------------------------------------- #
def make_task(task_id, *, time="", pet_id="p1", frequency="once",
              due_date="", priority=0, completed=False):
    """Build a Task with sensible defaults; override only what a test cares about."""
    return Task(
        id=task_id,
        pet_id=pet_id,
        type="walk",
        scheduled_time=time,
        frequency=frequency,
        due_date=due_date,
        priority=priority,
        completed=completed,
    )


# --------------------------------------------------------------------------- #
# 0. Basics — task completion and attaching tasks to a pet.
# --------------------------------------------------------------------------- #
def test_mark_completed_changes_status():
    task = make_task("t1")

    assert task.completed is False  # starts incomplete
    task.mark_completed()
    assert task.completed is True   # status flipped to done


def test_adding_task_increases_pet_task_count():
    pet = Pet(id="p1", name="Rex", species="dog")

    assert len(pet.tasks) == 0
    pet.add_task(make_task("t1"))
    assert len(pet.tasks) == 1  # list grew by one


# --------------------------------------------------------------------------- #
# 1. Sorting correctness — tasks come back in chronological order.
# --------------------------------------------------------------------------- #
def test_sort_by_time_orders_chronologically():
    schedule = Schedule()
    tasks = [make_task("a", time="18:00"),
             make_task("b", time="08:00"),
             make_task("c", time="12:00")]

    ordered = schedule.sort_by_time(tasks)

    # We assert on the ids in their new order, so the result is unambiguous.
    assert [t.id for t in ordered] == ["b", "c", "a"]


def test_sort_by_time_pushes_untimed_tasks_to_end():
    # Edge case: a task with no scheduled_time ("") should sort LAST, not first,
    # because sort_by_time substitutes a "99:99" sentinel for empty times.
    schedule = Schedule()
    tasks = [make_task("untimed", time=""),
             make_task("morning", time="08:00")]

    ordered = schedule.sort_by_time(tasks)

    assert [t.id for t in ordered] == ["morning", "untimed"]


# --------------------------------------------------------------------------- #
# 2. Recurrence logic — completing a daily task queues the next day's copy.
# --------------------------------------------------------------------------- #
def test_completing_daily_task_creates_next_day_task():
    pet = Pet(id="p1", name="Rex", species="dog")
    today = date.today().isoformat()
    daily = make_task("feed", frequency="daily", due_date=today)
    pet.add_task(daily)

    follow_up = pet.complete_task("feed")

    # The original is now done...
    assert daily.completed is True
    # ...a follow-up was returned and appended to the pet...
    assert follow_up is not None
    assert follow_up in pet.tasks
    assert follow_up.completed is False
    # ...and it is dated exactly one day later.
    expected = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    assert follow_up.due_date == expected


def test_weekly_task_advances_seven_days():
    pet = Pet(id="p1", name="Rex", species="dog")
    start = "2026-01-01"
    weekly = make_task("bath", frequency="weekly", due_date=start)
    pet.add_task(weekly)

    follow_up = pet.complete_task("bath")

    assert follow_up.due_date == "2026-01-08"


def test_completing_one_off_task_creates_no_follow_up():
    # Edge case: a "once" task should NOT spawn a new task.
    pet = Pet(id="p1", name="Rex", species="dog")
    pet.add_task(make_task("vet-visit", frequency="once"))

    follow_up = pet.complete_task("vet-visit")

    assert follow_up is None
    assert len(pet.tasks) == 1  # nothing new appended


# --------------------------------------------------------------------------- #
# 3. Conflict detection — duplicate times are flagged.
# --------------------------------------------------------------------------- #
def test_detect_conflicts_flags_two_tasks_at_same_time():
    schedule = Schedule()
    tasks = [make_task("a", time="09:00", pet_id="p1"),
             make_task("b", time="09:00", pet_id="p2")]

    warnings = schedule.detect_conflicts(tasks)

    assert len(warnings) == 1
    assert "09:00" in warnings[0]


def test_detect_conflicts_clean_schedule_returns_empty():
    # Happy path: distinct times => no warnings, no crash.
    schedule = Schedule()
    tasks = [make_task("a", time="09:00"),
             make_task("b", time="10:00")]

    assert schedule.detect_conflicts(tasks) == []


def test_detect_conflicts_ignores_untimed_tasks():
    # Edge case: two tasks with no time are NOT a conflict.
    schedule = Schedule()
    tasks = [make_task("a", time=""), make_task("b", time="")]

    assert schedule.detect_conflicts(tasks) == []


# --------------------------------------------------------------------------- #
# Bonus edge case: an owner/pet with no tasks must not crash the planner.
# --------------------------------------------------------------------------- #
def test_daily_plan_for_owner_with_no_tasks_is_empty():
    owner = Owner(id="o1", name="Sam")
    owner.pets.append(Pet(id="p1", name="Rex", species="dog"))
    owner.schedule = Schedule()

    assert owner.get_daily_plan("2026-01-01") == []
