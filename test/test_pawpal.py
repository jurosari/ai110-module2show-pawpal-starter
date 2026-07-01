"""Basic tests for the PawPal+ logic layer.

Run from the project root with:  python -m pytest
"""

from pawpal_system import Pet, Schedule, Task


def test_mark_completed_changes_status():
    """Task Completion: marking a task complete flips its status to done."""
    task = Task(id="t1", pet_id="p1", type="Walk")

    assert task.completed is False  # starts incomplete

    task.mark_completed()

    assert task.completed is True  # status changed


def test_adding_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet grows its task list by one."""
    pet = Pet(id="p1", name="Rex", species="Dog", age=3)

    assert len(pet.tasks) == 0  # no tasks yet

    pet.add_task(Task(id="t1", pet_id="p1", type="Feeding"))

    assert len(pet.tasks) == 1  # count increased by one


def test_completing_daily_task_spawns_next_day():
    """Recurrence: finishing a daily task queues one due the next day."""
    pet = Pet(id="p1", name="Rex", species="Dog", age=3)
    pet.add_task(Task(id="t1", pet_id="p1", type="Walk",
                      frequency="daily", due_date="2026-06-30"))

    follow_up = pet.complete_task("t1")

    assert follow_up is not None            # a next occurrence was created
    assert follow_up.due_date == "2026-07-01"  # today + 1 day via timedelta
    assert follow_up.completed is False     # the new one starts incomplete
    assert len(pet.tasks) == 2              # original + follow-up


def test_completing_weekly_task_spawns_seven_days_later():
    """Recurrence: a weekly task repeats seven days out, rolling the month."""
    pet = Pet(id="p1", name="Luna", species="Cat", age=2)
    pet.add_task(Task(id="t2", pet_id="p1", type="Bath",
                      frequency="weekly", due_date="2026-06-30"))

    follow_up = pet.complete_task("t2")

    assert follow_up.due_date == "2026-07-07"  # +7 days across the boundary


def test_completing_one_off_task_does_not_repeat():
    """Recurrence: a one-off task creates no follow-up when completed."""
    pet = Pet(id="p1", name="Rex", species="Dog", age=3)
    pet.add_task(Task(id="t3", pet_id="p1", type="Vet visit"))

    follow_up = pet.complete_task("t3")

    assert follow_up is None       # nothing to repeat
    assert len(pet.tasks) == 1     # list unchanged


def test_detect_conflicts_flags_same_time_slot():
    """Conflict detection: two tasks at the same time produce a warning."""
    schedule = Schedule()
    tasks = [
        Task(id="t1", pet_id="p1", type="Feeding", scheduled_time="18:00"),
        Task(id="t2", pet_id="p2", type="Play", scheduled_time="18:00"),
        Task(id="t3", pet_id="p1", type="Walk", scheduled_time="08:00"),
    ]

    warnings = schedule.detect_conflicts(tasks)

    assert len(warnings) == 1       # only the 18:00 slot clashes
    assert "18:00" in warnings[0]


def test_detect_conflicts_returns_empty_when_clean():
    """Conflict detection: no clashes returns an empty list, never raises."""
    schedule = Schedule()
    tasks = [
        Task(id="t1", pet_id="p1", type="Walk", scheduled_time="08:00"),
        Task(id="t2", pet_id="p1", type="Feeding", scheduled_time="18:00"),
        Task(id="t3", pet_id="p2", type="Nap", scheduled_time=""),  # untimed
    ]

    assert schedule.detect_conflicts(tasks) == []
