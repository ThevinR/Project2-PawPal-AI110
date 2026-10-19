from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def show(label: str, tasks) -> None:
    print(f"\n{label}")
    print("-" * len(label))
    if not tasks:
        print("(none)")
    for t in tasks:
        when = f"{t.preferred_time:%H:%M}" if t.preferred_time else "any time"
        done = "done" if t.is_completed else "todo"
        print(
            f"{when:>8}  {t.title:<14} {t.pet_name:<5} "
            f"{t.duration_minutes:>3} min  [{t.priority.name.lower():<6}] {done}"
        )


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    rex = Pet(name="Rex", species="dog")
    mia = Pet(name="Mia", species="cat")
    owner.add_pet(rex)
    owner.add_pet(mia)

    # Deliberately added out of time order, mixed across pets.
    mia.add_task(Task("Play session", 20, Priority.MEDIUM, preferred_time=time(18, 0)))
    rex.add_task(Task("Grooming", 40, Priority.LOW, preferred_time=time(16, 0)))
    mia.add_task(Task("Medication", 5, Priority.HIGH, preferred_time=time(12, 0)))
    rex.add_task(Task("Fetch", 15, Priority.MEDIUM))  # no preferred time
    rex.add_task(Task("Morning walk", 30, Priority.HIGH, preferred_time=time(7, 30)))
    mia.add_task(Task("Breakfast", 10, Priority.HIGH, preferred_time=time(8, 0)))

    # Mark a couple done so the completion filter has something to show.
    rex.tasks[-1].mark_complete()  # Morning walk
    mia.tasks[0].mark_complete()  # Play session

    scheduler = Scheduler(owner)
    tasks = scheduler.get_tasks()

    show("As added (out of order)", tasks)
    show("sort_by_time", scheduler.sort_by_time(tasks))
    show("sort_tasks (priority, then time, then length)", scheduler.sort_tasks(tasks))
    show("filter_tasks: pet_name='Rex'", scheduler.filter_tasks(tasks, pet_name="Rex"))
    show("filter_tasks: completed=True", scheduler.filter_tasks(tasks, completed=True))
    show(
        "filter_tasks: pet_name='Mia', completed=False, sorted by time",
        scheduler.sort_by_time(
            scheduler.filter_tasks(tasks, pet_name="Mia", completed=False)
        ),
    )

    print("\nConflict check before adding a clash")
    print("------------------------------------")
    print(scheduler.conflict_warnings(scheduler.get_tasks()) or "No conflicts.")

    # Two tasks at exactly the same time (09:00), one for each pet.
    rex.add_task(Task("Vet call", 20, Priority.MEDIUM, preferred_time=time(9, 0)))
    mia.add_task(Task("Brushing", 10, Priority.LOW, preferred_time=time(9, 0)))
    print("\nConflict check after adding two tasks at 09:00")
    print("----------------------------------------------")
    warnings = scheduler.conflict_warnings(scheduler.get_tasks())
    print("\n".join(warnings) or "No conflicts.")

    plan = scheduler.generate_plan()
    show(f"Today's plan ({owner.available_minutes} min available)", scheduler.sort_by_time(plan))
    print("\nWhy this plan:")
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
