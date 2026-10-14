from dataclasses import dataclass, field
from datetime import date, time
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
    last_completed: Optional[date] = None  # lets recurring tasks reset each day
    id: str = field(default_factory=lambda: uuid4().hex)

    def mark_complete(self, on: Optional[date] = None) -> None:
        pass

    def is_due(self, on: date) -> bool:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: str) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    day_start: time = time(8, 0)  # when the plan begins, so tasks get real start times
    preferences: dict = field(default_factory=dict)  # TODO: decide which keys the scheduler reads
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass


@dataclass
class ScheduledItem:
    task: Task
    start_time: time
    reason: str


@dataclass
class SkippedTask:
    task: Task
    reason: str  # e.g. "not enough time left"


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.plan: List[ScheduledItem] = []
        self.skipped: List[SkippedTask] = []

    def generate_plan(self, on: Optional[date] = None) -> List[ScheduledItem]:
        """Clear any previous plan and skipped list, then build a fresh plan."""
        pass

    def explain_plan(self) -> str:
        pass
