from dataclasses import dataclass, field
from datetime import time
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
    id: str = field(default_factory=lambda: uuid4().hex)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet and add it to the pet's task list."""
        task.pet_name = self.name
        self.tasks.append(task)

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
        """Highest priority first, then earliest preferred time, then shortest."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority.value,
                t.preferred_time is None,
                t.preferred_time or time.max,
                t.duration_minutes,
            ),
        )

    def filter_tasks(
        self,
        tasks: List[Task],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Keep only tasks matching the given pet name and/or completion status."""
        result = tasks
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        if completed is not None:
            result = [t for t in result if t.is_completed == completed]
        return result

    def detect_conflicts(self, tasks: List[Task]) -> List[tuple]:
        """Pairs of tasks whose preferred-time windows overlap."""
        timed = [t for t in tasks if t.preferred_time is not None]
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

    def generate_plan(self) -> List[Task]:
        """Fit the highest-priority pending tasks into the owner's available time."""
        pending = self.filter_tasks(self.get_tasks(), completed=False)
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
        for a, b in self.detect_conflicts(self.plan):
            lines.append(f"- Conflict: '{a.title}' overlaps '{b.title}'")
        return "\n".join(lines)
