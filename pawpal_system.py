from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "high" | "medium" | "low"
    preferred_time: Optional[str] = None  # e.g. "08:00"
    frequency: str = "daily"  # "daily" | "weekly" | "once"
    is_completed: bool = False

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass


@dataclass
class ScheduledItem:
    task: Task
    start_time: str
    reason: str


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.plan: List[ScheduledItem] = []
        self.skipped: List[Task] = []

    def generate_plan(self) -> List[ScheduledItem]:
        pass

    def explain_plan(self) -> str:
        pass
