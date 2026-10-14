from pawpal_system import Pet, Priority, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, Priority.HIGH)
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Rex", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10, Priority.HIGH))

    assert len(pet.tasks) == 1
