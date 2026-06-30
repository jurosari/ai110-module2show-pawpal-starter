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

    # Pet 1: a dog.
    rex = Pet(id="p1", name="Rex", species="Dog", age=3)
    owner.add_pet(rex)
    rex.add_task(Task(id="t1", pet_id="p1", type="Morning walk",
                      scheduled_time="08:00", duration_minutes=30, priority=5))
    rex.add_task(Task(id="t2", pet_id="p1", type="Feeding",
                      scheduled_time="18:00", duration_minutes=10, priority=4))

    # Pet 2: a cat.
    luna = Pet(id="p2", name="Luna", species="Cat", age=2)
    owner.add_pet(luna)
    luna.add_task(Task(id="t3", pet_id="p2", type="Medication",
                       scheduled_time="12:00", duration_minutes=5, priority=9))
    luna.add_task(Task(id="t4", pet_id="p2", type="Play / enrichment",
                       scheduled_time="18:00", duration_minutes=15, priority=2))

    return owner


def pet_name_for(owner: Owner, pet_id: str) -> str:
    """Look up a pet's display name by id."""
    for pet in owner.pets:
        if pet.id == pet_id:
            return pet.name
    return "?"


def main() -> None:
    owner = build_demo_owner()

    print(f"=== Today's Schedule for {owner.name} ===\n")

    plan = owner.get_daily_plan(date="2026-06-30")
    if not plan:
        print("  Nothing scheduled today!")
        return

    for task in plan:
        pet_name = pet_name_for(owner, task.pet_id)
        print(
            f"  {task.scheduled_time}  {task.type} "
            f"for {pet_name} ({task.duration_minutes} min) "
            f"[priority: {task.priority}]"
        )

    print(f"\n{len(plan)} task(s) planned across {len(owner.pets)} pets.")


if __name__ == "__main__":
    main()
