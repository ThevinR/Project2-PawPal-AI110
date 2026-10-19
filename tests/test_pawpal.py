from datetime import date, time, timedelta

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task


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


def _scheduler(*tasks, minutes=120):
    owner = Owner(name="Jordan", available_minutes=minutes)
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    for t in tasks:
        pet.add_task(t)
    return Scheduler(owner), pet


def test_sort_by_time_is_chronological_with_untimed_last():
    a = Task("Late", 10, Priority.LOW, preferred_time=time(18, 0))
    b = Task("Untimed", 10, Priority.LOW)
    c = Task("Early", 10, Priority.LOW, preferred_time=time(7, 0))
    sched, _ = _scheduler(a, b, c)

    assert [t.title for t in sched.sort_by_time([a, b, c])] == ["Early", "Late", "Untimed"]


def test_filter_by_pet_and_status():
    owner = Owner(name="J", available_minutes=60)
    rex, mia = Pet("Rex", "dog"), Pet("Mia", "cat")
    owner.add_pet(rex)
    owner.add_pet(mia)
    done = Task("Walk", 10, Priority.LOW, frequency=Frequency.ONCE)
    rex.add_task(done)
    rex.add_task(Task("Feed", 5, Priority.LOW))
    mia.add_task(Task("Play", 5, Priority.LOW))
    done.mark_complete()
    sched = Scheduler(owner)
    tasks = sched.get_tasks()

    assert [t.title for t in sched.filter_tasks(tasks, pet_name="Rex")] == ["Walk", "Feed"]
    assert [t.title for t in sched.filter_tasks(tasks, completed=True)] == ["Walk"]
    assert [t.title for t in sched.filter_tasks(tasks, pet_name="Rex", completed=False)] == ["Feed"]


def test_completing_daily_task_creates_next_day_occurrence():
    task = Task("Feed", 5, Priority.HIGH, frequency=Frequency.DAILY)
    _, pet = _scheduler(task)
    today = task.due_date

    nxt = pet.complete_task(task.id)

    assert task.is_completed is True
    assert nxt is not None and nxt.is_completed is False
    assert nxt.due_date == today + timedelta(days=1)
    assert nxt.pet_name == "Rex" and nxt in pet.tasks and nxt.id != task.id


def test_completing_weekly_task_moves_due_date_a_week():
    task = Task("Bath", 20, Priority.LOW, frequency=Frequency.WEEKLY)
    nxt = task.mark_complete()
    assert nxt.due_date == task.due_date + timedelta(weeks=1)


def test_one_off_task_does_not_recur():
    task = Task("Vet", 60, Priority.HIGH, frequency=Frequency.ONCE)
    _, pet = _scheduler(task)

    assert pet.complete_task(task.id) is None
    assert len(pet.tasks) == 1


def test_plan_excludes_tasks_not_yet_due():
    task = Task("Feed", 5, Priority.HIGH)
    sched, pet = _scheduler(task)
    nxt = pet.complete_task(task.id)

    assert sched.generate_plan() == []
    assert sched.generate_plan(today=nxt.due_date) == [nxt]


def test_conflict_detected_for_overlapping_times():
    a = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Feed", 10, Priority.HIGH, preferred_time=time(8, 15))
    sched, _ = _scheduler(a, b)

    assert sched.detect_conflicts([a, b]) == [(a, b)]
    warnings = sched.conflict_warnings([a, b])
    assert len(warnings) == 1 and "Walk" in warnings[0] and "Feed" in warnings[0]


def test_conflict_detected_across_different_pets_and_labelled():
    owner = Owner(name="Jordan", available_minutes=120)
    rex, mia = Pet("Rex", "dog"), Pet("Mia", "cat")
    owner.add_pet(rex)
    owner.add_pet(mia)
    a = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Breakfast", 10, Priority.HIGH, preferred_time=time(8, 0))
    c = Task("Brush", 10, Priority.LOW, preferred_time=time(8, 5))
    rex.add_task(a)
    mia.add_task(b)
    rex.add_task(c)
    sched = Scheduler(owner)

    warnings = sched.conflict_warnings(sched.get_tasks())

    assert len(warnings) == 3
    assert sum("different pets" in w for w in warnings) == 2
    assert sum("same pet" in w for w in warnings) == 1


def test_conflict_check_warns_instead_of_crashing_on_bad_time():
    a = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Feed", 10, Priority.HIGH, preferred_time=time(8, 10))
    bad = Task("Odd", 10, Priority.LOW, preferred_time="8am")  # not a time
    sched, _ = _scheduler(a, b, bad)

    warnings = sched.conflict_warnings([a, b, bad])

    assert len(warnings) == 1 and "Walk" in warnings[0]


def test_back_to_back_and_untimed_tasks_do_not_conflict():
    a = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Feed", 10, Priority.HIGH, preferred_time=time(8, 30))
    c = Task("Play", 10, Priority.LOW)
    sched, _ = _scheduler(a, b, c)

    assert sched.conflict_warnings([a, b, c]) == []
