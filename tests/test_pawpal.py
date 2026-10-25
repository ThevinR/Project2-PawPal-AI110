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


# --- Sorting correctness ---------------------------------------------------


def test_sort_tasks_orders_by_priority_then_time_then_duration():
    low = Task("Brush", 10, Priority.LOW, preferred_time=time(6, 0))
    high_late = Task("Vet", 10, Priority.HIGH, preferred_time=time(17, 0))
    high_early_long = Task("Walk", 45, Priority.HIGH, preferred_time=time(7, 0))
    high_early_short = Task("Feed", 5, Priority.HIGH, preferred_time=time(7, 0))
    med = Task("Play", 10, Priority.MEDIUM, preferred_time=time(9, 0))
    sched, _ = _scheduler(low, high_late, high_early_long, high_early_short, med)

    order = [t.title for t in sched.sort_tasks([low, high_late, high_early_long, high_early_short, med])]

    # HIGH block first; inside it, 07:00 before 17:00; the two 07:00 tasks break
    # their tie on duration, so the 5-minute Feed precedes the 45-minute Walk.
    assert order == ["Feed", "Walk", "Vet", "Play", "Brush"]


def test_timed_task_sorts_before_untimed_task_of_same_priority():
    untimed = Task("Anytime", 5, Priority.MEDIUM)
    timed = Task("Noon", 5, Priority.MEDIUM, preferred_time=time(12, 0))
    sched, _ = _scheduler(untimed, timed)

    assert [t.title for t in sched.sort_tasks([untimed, timed])] == ["Noon", "Anytime"]


def test_identical_tasks_keep_insertion_order_in_both_sorts():
    first = Task("First", 10, Priority.HIGH, preferred_time=time(8, 0))
    second = Task("Second", 10, Priority.HIGH, preferred_time=time(8, 0))
    sched, _ = _scheduler(first, second)

    # Every sort key ties, so Python's stable sort must preserve the input order.
    assert [t.title for t in sched.sort_tasks([first, second])] == ["First", "Second"]
    assert [t.title for t in sched.sort_by_time([first, second])] == ["First", "Second"]


def test_sort_by_time_ignores_priority_while_sort_tasks_respects_it():
    low_early = Task("Low early", 10, Priority.LOW, preferred_time=time(7, 0))
    high_late = Task("High late", 10, Priority.HIGH, preferred_time=time(9, 0))
    sched, _ = _scheduler(low_early, high_late)

    assert [t.title for t in sched.sort_by_time([low_early, high_late])] == ["Low early", "High late"]
    assert [t.title for t in sched.sort_tasks([low_early, high_late])] == ["High late", "Low early"]


def test_sorts_return_new_lists_and_handle_empty_input():
    a = Task("A", 10, Priority.LOW, preferred_time=time(9, 0))
    b = Task("B", 10, Priority.HIGH, preferred_time=time(8, 0))
    original = [a, b]
    sched, _ = _scheduler(a, b)

    assert sched.sort_tasks(original) is not original
    assert original == [a, b]  # input untouched
    assert sched.sort_tasks([]) == []
    assert sched.sort_by_time([]) == []


# --- Recurrence logic ------------------------------------------------------


def test_daily_recurrence_leaves_original_completed_and_adds_one_task():
    task = Task("Feed", 5, Priority.HIGH, frequency=Frequency.DAILY)
    _, pet = _scheduler(task)

    nxt = pet.complete_task(task.id)

    assert len(pet.tasks) == 2
    assert pet.tasks[0] is task and task.is_completed is True
    assert pet.tasks[1] is nxt
    # The copy inherits everything but status, date and identity.
    assert (nxt.title, nxt.duration_minutes, nxt.priority, nxt.frequency) == (
        "Feed", 5, Priority.HIGH, Frequency.DAILY
    )


def test_weekly_recurrence_crosses_a_month_boundary():
    task = Task("Bath", 20, Priority.LOW, frequency=Frequency.WEEKLY,
                due_date=date(2026, 1, 28))

    nxt = task.mark_complete()

    assert nxt.due_date == date(2026, 2, 4)


def test_completing_an_unknown_id_is_a_no_op():
    task = Task("Feed", 5, Priority.HIGH)
    _, pet = _scheduler(task)

    assert pet.complete_task("not-a-real-id") is None
    assert len(pet.tasks) == 1 and task.is_completed is False


def test_removing_a_task_by_id_and_ignoring_unknown_ids():
    a = Task("Feed", 5, Priority.HIGH)
    b = Task("Walk", 30, Priority.HIGH)
    _, pet = _scheduler(a, b)

    pet.remove_task("not-a-real-id")
    assert len(pet.tasks) == 2

    pet.remove_task(a.id)
    assert [t.title for t in pet.tasks] == ["Walk"]


def test_completing_the_same_task_twice_recurs_twice():
    """Documents current behaviour: completing an already-done task recurs again.

    mark_complete() does not check is_completed, so a second call spawns another
    occurrence stepped from the SAME due_date, producing a duplicate. If PawPal+
    should treat re-completion as a no-op, this test is the one to flip.
    """
    task = Task("Feed", 5, Priority.HIGH, frequency=Frequency.DAILY)
    _, pet = _scheduler(task)

    first = pet.complete_task(task.id)
    second = pet.complete_task(task.id)

    assert first.due_date == second.due_date
    assert len(pet.tasks) == 3


# --- Conflict detection ----------------------------------------------------


def test_duplicate_times_are_flagged_as_a_conflict():
    a = Task("Feed", 10, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Medicate", 10, Priority.HIGH, preferred_time=time(8, 0))
    sched, _ = _scheduler(a, b)

    assert sched.detect_conflicts([a, b]) == [(a, b)]
    assert len(sched.conflict_warnings([a, b])) == 1


def test_zero_duration_task_never_conflicts():
    """A 0-minute task occupies an empty window, so the overlap test is false."""
    instant = Task("Check water", 0, Priority.LOW, preferred_time=time(8, 0))
    walk = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    sched, _ = _scheduler(instant, walk)

    assert sched.detect_conflicts([instant, walk]) == []


def test_task_running_past_midnight_does_not_wrap_around():
    """Documents a known limitation: _minutes() has no midnight wraparound.

    A 23:50 task lasting 30 minutes ends at minute 1460, past the end of the
    day, so it is not compared against early-morning tasks of the next day.
    """
    late = Task("Night walk", 30, Priority.HIGH, preferred_time=time(23, 50))
    early = Task("Early feed", 10, Priority.HIGH, preferred_time=time(0, 5))
    sched, _ = _scheduler(late, early)

    assert sched.detect_conflicts([late, early]) == []


def test_no_conflicts_on_empty_or_single_task_lists():
    only = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    sched, _ = _scheduler(only)

    assert sched.detect_conflicts([]) == []
    assert sched.conflict_warnings([]) == []
    assert sched.detect_conflicts([only]) == []


# --- Planning and empty states ---------------------------------------------


def test_pet_with_no_tasks_produces_an_empty_plan():
    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(Pet("Rex", "dog"))
    sched = Scheduler(owner)

    assert sched.get_tasks() == []
    assert sched.generate_plan() == []
    assert sched.skipped == []
    assert sched.explain_plan() == "No plan yet, or no pending tasks."


def test_owner_with_no_pets_produces_an_empty_plan():
    sched = Scheduler(Owner(name="Jordan", available_minutes=120))

    assert sched.generate_plan() == []
    assert sched.explain_plan() == "No plan yet, or no pending tasks."


def test_plan_fits_every_task_when_budget_is_exact():
    a = Task("Walk", 40, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Feed", 20, Priority.HIGH, preferred_time=time(9, 0))
    sched, _ = _scheduler(a, b, minutes=60)

    plan = sched.generate_plan()

    assert [t.title for t in plan] == ["Walk", "Feed"]
    assert sched.skipped == []
    assert sum(t.duration_minutes for t in plan) == 60


def test_oversized_task_is_skipped_but_a_later_shorter_task_still_fits():
    """The greedy loop keeps going after a skip, so one huge task cannot
    starve the rest of the day."""
    huge = Task("Grooming", 90, Priority.HIGH, preferred_time=time(8, 0))
    small = Task("Feed", 10, Priority.HIGH, preferred_time=time(9, 0))
    sched, _ = _scheduler(huge, small, minutes=30)

    plan = sched.generate_plan()

    assert [t.title for t in plan] == ["Feed"]
    assert [t.title for t in sched.skipped] == ["Grooming"]


def test_zero_available_minutes_skips_everything():
    task = Task("Feed", 5, Priority.HIGH)
    sched, _ = _scheduler(task, minutes=0)

    assert sched.generate_plan() == []
    assert [t.title for t in sched.skipped] == ["Feed"]
    assert "Planned 0 of 0 available minutes" in sched.explain_plan()


def test_plan_excludes_completed_tasks_and_includes_overdue_ones():
    overdue = Task("Feed", 5, Priority.HIGH, due_date=date.today() - timedelta(days=2))
    done = Task("Walk", 30, Priority.HIGH, frequency=Frequency.ONCE)
    sched, pet = _scheduler(overdue, done)
    pet.complete_task(done.id)

    assert [t.title for t in sched.generate_plan()] == ["Feed"]


def test_regenerating_a_plan_resets_previous_results():
    huge = Task("Grooming", 90, Priority.HIGH)
    sched, _ = _scheduler(huge, minutes=30)

    sched.generate_plan()
    sched.generate_plan()

    assert len(sched.skipped) == 1  # not appended to across runs


def test_explain_plan_reports_planned_skipped_and_conflicts():
    a = Task("Walk", 30, Priority.HIGH, preferred_time=time(8, 0))
    b = Task("Medicate", 10, Priority.HIGH, preferred_time=time(8, 15))
    too_big = Task("Grooming", 500, Priority.LOW)
    sched, _ = _scheduler(a, b, too_big, minutes=60)

    sched.generate_plan()
    text = sched.explain_plan()

    assert "Planned 40 of 60 available minutes" in text
    assert "Rex: Walk (30 min, high) at 08:00" in text
    assert "Skipped Rex: Grooming" in text and "not enough time left" in text
    assert "Warning (same pet)" in text
