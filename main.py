"""Testing ground for the PawPal+ logic layer.

Builds an owner with two pets and a few tasks, then prints today's schedule
to the terminal. Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Schedule


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and several care tasks."""
    owner = Owner(id="o1", name="Alex")
    owner.set_availability(
        days=["Mon", "Tue", "Wed", "Thu", "Fri"],
        times=["08:00", "12:00", "18:00"],
    )
    owner.update_preferences({"preferred_times": ["08:00", "18:00"]})

    # The Schedule is the "brain" the owner delegates planning to.
    owner.schedule = Schedule(
        days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri"],
        timeslots=["08:00", "12:00", "18:00"],
    )

    # Pet 1: a dog. Tasks are added OUT OF TIME ORDER on purpose so we can
    # prove the sorting logic actually reorders them (evening before morning).
    rex = Pet(id="p1", name="Rex", species="Dog", age=3)
    owner.add_pet(rex)
    rex.add_task(Task(id="t2", pet_id="p1", type="Evening feeding",
                      scheduled_time="18:00", duration_minutes=10, priority=4))
    rex.add_task(Task(id="t1", pet_id="p1", type="Morning walk",
                      scheduled_time="08:00", duration_minutes=30, priority=5,
                      frequency="daily", due_date="2026-06-30"))

    # Pet 2: a cat. Also added out of order.
    luna = Pet(id="p2", name="Luna", species="Cat", age=2)
    owner.add_pet(luna)
    # Deliberately at 18:00 — same slot as Rex's evening feeding — so the
    # conflict detector has a real clash to catch.
    luna.add_task(Task(id="t4", pet_id="p2", type="Play / enrichment",
                       scheduled_time="18:00", duration_minutes=15, priority=2))
    luna.add_task(Task(id="t3", pet_id="p2", type="Medication",
                       scheduled_time="12:00", duration_minutes=5, priority=9))

    # Mark one task done so the "pending only" filter has something to hide.
    luna.tasks[-1].mark_completed()  # Medication already given

    return owner


def pet_name_for(owner: Owner, pet_id: str) -> str:
    """Look up a pet's display name by id."""
    for pet in owner.pets:
        if pet.id == pet_id:
            return pet.name
    return "?"


def print_task(owner: Owner, task: Task) -> None:
    """Print one task line with its pet's name."""
    pet_name = pet_name_for(owner, task.pet_id)
    status = "done" if task.completed else f"priority: {task.priority}"
    print(
        f"  {task.scheduled_time or '--:--'}  {task.type} "
        f"for {pet_name} ({task.duration_minutes} min) "
        f"[{status}]"
    )


def main() -> None:
    owner = build_demo_owner()
    schedule = owner.schedule
    all_tasks = owner.get_all_tasks()

    # --- Sorting: order every task chronologically by "HH:MM" -------------
    print(f"=== All tasks for {owner.name}, sorted by time ===\n")
    for task in schedule.sort_by_time(all_tasks):
        print_task(owner, task)

    # --- Filtering by status: hide completed tasks ------------------------
    print("\n=== Pending tasks only (completed hidden), sorted by time ===\n")
    pending = schedule.filter_tasks(all_tasks, completed=False)
    for task in schedule.sort_by_time(pending):
        print_task(owner, task)

    # --- Filtering by pet: just Luna's schedule ---------------------------
    luna = next(p for p in owner.pets if p.name == "Luna")
    print(f"\n=== {luna.name}'s tasks, sorted by time ===\n")
    luna_tasks = schedule.filter_tasks(all_tasks, pet_id=luna.id)
    for task in schedule.sort_by_time(luna_tasks):
        print_task(owner, task)

    print(
        f"\n{len(pending)} pending task(s) across {len(owner.pets)} pets "
        f"({len(all_tasks)} total)."
    )

    # --- Conflict detection: warn on tasks sharing a time slot ------------
    pet_names = {p.id: p.name for p in owner.pets}
    print("\n=== Checking for scheduling conflicts ===\n")
    conflicts = schedule.detect_conflicts(all_tasks, pet_names)
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts — every task has its own time slot.")

    # --- Recurring tasks: completing a daily task spawns tomorrow's --------
    rex = next(p for p in owner.pets if p.name == "Rex")
    walk = next(t for t in rex.tasks if t.id == "t1")
    print("\n=== Completing Rex's daily 'Morning walk' (due "
          f"{walk.due_date}) ===\n")
    follow_up = rex.complete_task("t1")
    print(f"  Marked '{walk.type}' complete: {walk.completed}")
    if follow_up is not None:
        print(f"  Auto-created next occurrence: due {follow_up.due_date} "
              f"at {follow_up.scheduled_time} (id {follow_up.id})")
    print(f"\n  Rex now has {len(rex.tasks)} task(s); "
          f"{len(rex.get_pending_tasks())} pending.")


if __name__ == "__main__":
    main()
