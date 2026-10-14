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

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
