# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation Summary

PawPal+ is built from four classes in `pawpal_system.py`.

- **Task** is one care activity. It holds a title, duration, priority, preferred time, frequency, and completion status, plus a unique id and the name of its pet.
- **Pet** stores the pet's name and species and keeps its own list of tasks. `add_task` links a task to the pet, and `remove_task` removes one by id.
- **Owner** holds the owner's name, the minutes available each day, and a list of pets. `get_all_tasks()` returns every pet's tasks in one list.
- **Scheduler** is the brain. It reads tasks through `Owner.get_all_tasks()`, so every pet is included, then sorts them (highest priority first, then earliest preferred time, then shortest). It filters out completed tasks and fits as many as possible into the owner's available time. It also detects overlapping preferred times and explains its choices in plain language.

**How they fit together:** an Owner has Pets, a Pet has Tasks, and the Scheduler depends only on the Owner. `generate_plan()` collects all pending tasks, keeps the highest-priority ones that fit in the time available, and records the rest as skipped. `explain_plan()` then reports what was planned, what was skipped and why, and any conflicts. `main.py` shows this end to end with one owner, two pets, and five tasks.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
- Rex: Morning walk (30 min, high) at 07:30
- Mia: Breakfast (10 min, high) at 08:00
- Mia: Medication (5 min, high) at 12:00
- Mia: Play session (20 min, medium) at 18:00
- Skipped Rex: Grooming (40 min, low): not enough time left
```

## 🧪 Testing PawPal+

Run the full suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite in `tests/test_pawpal.py` has 34 tests across the behaviors that matter most for a scheduler, split between happy paths and edge cases.

| Area | Happy paths | Edge cases |
|------|-------------|------------|
| **Sorting** | `sort_tasks` applies all three keys in order (priority → preferred time → duration); `sort_by_time` is chronological | Timed tasks sort before untimed ones of the same priority; identical tasks keep insertion order via Python's stable sort; the two sorts deliberately disagree on a low-priority-early vs. high-priority-late pair; empty lists and input-not-mutated |
| **Recurrence** | Completing a `DAILY` task adds one new pending task due the next day with a new id; `WEEKLY` advances seven days | `ONCE` tasks don't recur; weekly recurrence across a month boundary (Jan 28 → Feb 4); unknown task ids are a no-op for both `complete_task` and `remove_task`; completing a task twice recurs twice (documented, see below) |
| **Conflict detection** | Two tasks at the exact same time are flagged; overlapping windows are flagged within one pet and across pets, and labelled accordingly | Back-to-back tasks don't conflict (half-open windows); untimed tasks are ignored; an invalid `preferred_time` warns instead of crashing; zero-duration tasks never conflict; a task running past midnight does not wrap around (documented, see below); empty and single-task lists |
| **Plan generation** | Tasks that fit the budget are all planned; an exact-fit budget leaves nothing skipped; `explain_plan` reports planned minutes, skip reasons and conflicts | A pet with no tasks and an owner with no pets both yield an empty plan; zero available minutes skips everything; an oversized task is skipped but a later shorter task still fits; completed tasks excluded and overdue ones included; re-running `generate_plan` resets prior results |

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\thevi\Project2-PawPal-AI110
plugins: anyio-4.15.1
collected 34 items

tests\test_pawpal.py ..................................                  [100%]

============================= 34 passed in 0.04s ==============================
```

### Confidence level: ★★★★☆ (4 / 5)

Every documented behavior is covered by a passing test, including the empty-state and tie-breaking cases that usually hide bugs, so I'd trust the core scheduling logic. One star is held back for two limitations the tests *document* rather than fix:

- **Midnight wraparound.** `_minutes()` has no modulo, so a 23:50 task lasting 30 minutes never conflicts with a 00:05 task the next morning.
- **Double completion.** `Task.mark_complete()` doesn't check `is_completed`, so completing an already-finished recurring task spawns a duplicate next occurrence from the same `due_date`.

Both are deliberate known behaviors with tests pinning them down, so a future fix will be caught immediately — but until they're resolved the system isn't fully reliable at those boundaries.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | Planning order, and chronological order |
| Filtering | `Scheduler.filter_tasks()` | By pet name and/or completion status |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warnings()` | Overlapping time windows, reported as warnings |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()` | Daily and weekly tasks get a next occurrence |

### Sorting

- **`Scheduler.sort_tasks(tasks)`** orders tasks for planning: highest priority first, then earliest preferred time, then shortest duration. Tasks with no preferred time come after timed tasks of the same priority.
- **`Scheduler.sort_by_time(tasks)`** orders tasks chronologically by `preferred_time` and ignores priority. Tasks with no time go last, and tasks sharing a time keep their original order.
- Both return a new list and leave the input unchanged.

### Filtering

- **`Scheduler.filter_tasks(tasks, pet_name=None, completed=None)`** keeps only matching tasks.
- `pet_name` keeps one pet's tasks. `completed=True` keeps done tasks, `completed=False` keeps pending ones, and `None` does not filter on completion.
- The two filters combine, so `filter_tasks(tasks, pet_name="Rex", completed=False)` returns Rex's pending tasks.
- `generate_plan()` uses it to leave completed tasks out of the plan.

### Conflict detection

- **`Scheduler.detect_conflicts(tasks)`** returns pairs of tasks whose time windows overlap. A task occupies `preferred_time` up to `preferred_time + duration`, so a 30-minute task at 07:30 conflicts with one at 07:45. Back-to-back tasks do not conflict.
- It works within one pet and across different pets. Tasks with no valid `preferred_time` are skipped.
- **`Scheduler.conflict_warnings(tasks)`** turns those pairs into messages and never raises:

  ```
  Warning (different pets): 'Vet call' (Rex, 09:00) overlaps 'Brushing' (Mia, 09:00)
  ```

- This is a lightweight check: it only warns. It does not move or drop tasks, so a plan can still contain a clash. `explain_plan()` includes the warnings for the planned tasks.
- It compares every pair, which is O(n²). That is fine for a day's worth of tasks.

### Recurring tasks

- Each task has a `frequency` of `ONCE`, `DAILY` or `WEEKLY` and a `due_date`.
- **`Task.mark_complete()`** marks the task done. For `DAILY` and `WEEKLY` tasks it returns a fresh pending copy due one day or one week later, with a new id. `ONCE` tasks return `None`.
- **`Pet.complete_task(task_id)`** finds a task by id, completes it, and adds the next occurrence to the pet's tasks.
- `generate_plan(today=None)` only plans tasks whose `due_date` is on or before `today`, so the next occurrence doesn't appear until its day.

### Plan generation

**`Scheduler.generate_plan()`** goes through pending tasks in `sort_tasks` order and adds each one that fits in the owner's remaining minutes. A task that doesn't fit is skipped, but a later, shorter one can still fit. Clock times are not enforced.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
