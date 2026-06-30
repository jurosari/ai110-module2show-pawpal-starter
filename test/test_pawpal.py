"""Basic tests for the PawPal+ logic layer.

Run from the project root with:  python -m pytest
"""

from pawpal_system import Pet, Task


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
