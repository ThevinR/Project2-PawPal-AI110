from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    rex = Pet(name="Rex", species="dog")
    mia = Pet(name="Mia", species="cat")
    owner.add_pet(rex)
    owner.add_pet(mia)

    rex.add_task(Task("Morning walk", 30, Priority.HIGH, preferred_time=time(7, 30)))
    rex.add_task(Task("Grooming", 40, Priority.LOW, preferred_time=time(16, 0)))
    mia.add_task(Task("Breakfast", 10, Priority.HIGH, preferred_time=time(8, 0)))
    mia.add_task(Task("Medication", 5, Priority.HIGH, preferred_time=time(12, 0)))
    mia.add_task(Task("Play session", 20, Priority.MEDIUM, preferred_time=time(18, 0)))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print(f"Today's Schedule for {owner.name} ({owner.available_minutes} min available)")
    print("=" * 56)
    for task in sorted(plan, key=lambda t: t.preferred_time or time.max):
        when = f"{task.preferred_time:%H:%M}" if task.preferred_time else "any time"
        print(
            f"{when:>8}  {task.title:<14} {task.pet_name:<5} "
            f"{task.duration_minutes:>3} min  [{task.priority.name.lower()}]"
        )

    print()
    print("Why this plan:")
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
