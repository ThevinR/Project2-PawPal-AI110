from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from enum import Enum
from typing import List, Optional
from uuid import uuid4


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    pet_name: str = ""  # set by Pet.add_task so plans can say whose task it is
    preferred_time: Optional[time] = None
    frequency: Frequency = Frequency.DAILY
    is_completed: bool = False
    due_date: date = field(default_factory=date.today)
    id: str = field(default_factory=lambda: uuid4().hex)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as done; return the next occurrence if it recurs.

        DAILY tasks recur one day later and WEEKLY tasks one week later, as a
        fresh pending copy with a new id. ONCE tasks return None.
        """
        self.is_completed = True
        if self.frequency == Frequency.DAILY:
            step = timedelta(days=1)
        elif self.frequency == Frequency.WEEKLY:
            step = timedelta(weeks=1)
        else:
            return None
        return replace(
            self, is_completed=False, due_date=self.due_date + step, id=uuid4().hex
        )


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet and add it to the pet's task list."""
        task.pet_name = self.name
        self.tasks.append(task)

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Complete a task by id; recurring tasks get their next occurrence added.

        Returns the newly added next occurrence, or None if the task does not
        recur or no task has that id.
        """
        for task in self.tasks:
            if task.id == task_id:
                nxt = task.mark_complete()
                if nxt is not None:
                    self.add_task(nxt)
                return nxt
        return None

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.id != task_id]


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Every task across all of the owner's pets, in one list."""
        return [task for pet in self.pets for task in pet.tasks]


def _minutes(t: time) -> int:
    """Convert a time of day to minutes since midnight."""
    return t.hour * 60 + t.minute


class Scheduler:
    """The brain: pulls tasks across all of an owner's pets and organizes them."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.plan: List[Task] = []
        self.skipped: List[Task] = []

    def get_tasks(self) -> List[Task]:
        """Read tasks from the Owner so every pet is included."""
        return self.owner.get_all_tasks()

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Order tasks for planning: highest priority first, then earliest
        preferred time, then shortest duration.

        Tasks with no preferred time sort after timed tasks of the same priority.
        Returns a new list; the input is not modified.
        """
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority.value,
                t.preferred_time is None,
                t.preferred_time or time.max,
                t.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Order tasks chronologically by preferred time, ignoring priority.

        Tasks with no preferred time go last. The sort is stable, so tasks
        sharing a time keep their original relative order. Returns a new list.
        """
        return sorted(
            tasks,
            key=lambda t: (t.preferred_time is None, t.preferred_time or time.max),
        )

    def filter_tasks(
        self,
        tasks: List[Task],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Keep only tasks matching the given pet name and/or completion status.

        Args:
            tasks: Tasks to filter.
            pet_name: If given, keep only this pet's tasks.
            completed: If True keep done tasks, if False keep pending ones,
                if None do not filter on completion.

        Both filters combine (AND). Returns a list; the input is not modified.
        """
        result = tasks
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        if completed is not None:
            result = [t for t in result if t.is_completed == completed]
        return result

    def detect_conflicts(self, tasks: List[Task]) -> List[tuple]:
        """Find pairs of tasks whose preferred-time windows overlap.

        A task occupies [preferred_time, preferred_time + duration). Two tasks
        conflict when each starts before the other ends, so back-to-back tasks
        do not conflict. Works across pets and within one pet. Tasks without a
        valid preferred time are skipped rather than raising.

        Compares every pair, so it is O(n^2); fine for a day's worth of tasks.

        Returns:
            A list of (earlier_listed_task, later_listed_task) tuples.
        """
        # Skip anything without a usable time instead of raising on bad data.
        timed = [t for t in tasks if isinstance(t.preferred_time, time)]
        conflicts = []
        for i, a in enumerate(timed):
            a_start = _minutes(a.preferred_time)
            a_end = a_start + a.duration_minutes
            for b in timed[i + 1:]:
                b_start = _minutes(b.preferred_time)
                b_end = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    def conflict_warnings(self, tasks: List[Task]) -> List[str]:
        """Turn detected conflicts into warning strings; never raises.

        Each message says whether the clash is within one pet or between
        different pets. Returns an empty list when nothing overlaps.
        """
        return [
            f"Warning ({'same pet' if a.pet_name == b.pet_name else 'different pets'}): "
            f"'{a.title}' ({a.pet_name}, {a.preferred_time:%H:%M}) overlaps "
            f"'{b.title}' ({b.pet_name}, {b.preferred_time:%H:%M})"
            for a, b in self.detect_conflicts(tasks)
        ]

    def generate_plan(self, today: Optional[date] = None) -> List[Task]:
        """Greedily fit pending tasks due today into the owner's available time.

        Tasks are taken in sort_tasks order. Each one that fits in the remaining
        minutes goes into self.plan; any that does not goes into self.skipped
        (a later, shorter task can still fit). Clock times are not enforced, so
        planned tasks may still overlap; see conflict_warnings.

        Args:
            today: The date to plan for; defaults to date.today().

        Returns:
            The planned tasks, in planning order.
        """
        today = today or date.today()
        pending = [
            t
            for t in self.filter_tasks(self.get_tasks(), completed=False)
            if t.due_date <= today
        ]
        self.plan = []
        self.skipped = []
        remaining = self.owner.available_minutes
        for task in self.sort_tasks(pending):
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
        return self.plan

    def explain_plan(self) -> str:
        """Describe what was planned, what was skipped and why, and any conflicts."""
        if not self.plan and not self.skipped:
            return "No plan yet, or no pending tasks."
        used = sum(t.duration_minutes for t in self.plan)
        lines = [
            f"Planned {used} of {self.owner.available_minutes} available minutes "
            "(highest priority first, then earliest preferred time, then shortest)."
        ]
        for t in self.plan:
            at = f" at {t.preferred_time:%H:%M}" if t.preferred_time else ""
            lines.append(
                f"- {t.pet_name}: {t.title} ({t.duration_minutes} min, "
                f"{t.priority.name.lower()}){at}"
            )
        for t in self.skipped:
            lines.append(
                f"- Skipped {t.pet_name}: {t.title} "
                f"({t.duration_minutes} min, {t.priority.name.lower()}): not enough time left"
            )
        lines.extend(self.conflict_warnings(self.plan))
        return "\n".join(lines)
