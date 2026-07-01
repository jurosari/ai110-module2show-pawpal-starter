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

## 🖥️ Sample Output

Terminal output from running the logic-layer testing ground (`python main.py`).
It builds an owner with two pets and four tasks (added out of time order, with
one already completed), then demonstrates each Smarter Scheduling feature:
time sorting, filtering by status/pet, conflict detection, and recurrence.

```
=== All tasks for Alex, sorted by time ===

  08:00  Morning walk for Rex (30 min) [priority: 5]
  12:00  Medication for Luna (5 min) [done]
  18:00  Evening feeding for Rex (10 min) [priority: 4]
  18:00  Play / enrichment for Luna (15 min) [priority: 2]

=== Pending tasks only (completed hidden), sorted by time ===

  08:00  Morning walk for Rex (30 min) [priority: 5]
  18:00  Evening feeding for Rex (10 min) [priority: 4]
  18:00  Play / enrichment for Luna (15 min) [priority: 2]

=== Luna's tasks, sorted by time ===

  12:00  Medication for Luna (5 min) [done]
  18:00  Play / enrichment for Luna (15 min) [priority: 2]

3 pending task(s) across 2 pets (4 total).

=== Checking for scheduling conflicts ===

  [!] Conflict at 18:00: Evening feeding (Rex), Play / enrichment (Luna)

=== Completing Rex's daily 'Morning walk' (due 2026-06-30) ===

  Marked 'Morning walk' complete: True
  Auto-created next occurrence: due 2026-07-01 at 08:00 (id t1@2026-07-01)

  Rex now has 3 task(s); 2 pending.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
collected 7 items

test\test_pawpal.py .......                                              [100%]

============================== 7 passed in 0.07s ==============================
```

## 📐 Smarter Scheduling

These are the algorithmic features added on top of the base logic layer. Each
method lives in `pawpal_system.py` and is exercised by `main.py` and the tests
in `test/test_pawpal.py`.

| Feature | Method | Notes |
|---------|--------|-------|
| Sorting by time | `Schedule.sort_by_time(tasks)` | Chronological order via `sorted()` + lambda key |
| Filtering | `Schedule.filter_tasks(tasks, completed=..., pet_id=...)` | By completion status and/or pet |
| Conflict detection | `Schedule.detect_conflicts(tasks, pet_names=...)` | Warns on tasks sharing a time slot |
| Recurring tasks | `Pet.complete_task(task_id)` + `Task.next_occurrence()` | Auto-spawns the next daily/weekly occurrence |

### Sorting behavior — `Schedule.sort_by_time()`

Returns a new list of tasks ordered chronologically. Because `scheduled_time`
is a zero-padded 24-hour `"HH:MM"` string, plain string comparison already
matches clock order, so the `sorted()` key simply returns `t.scheduled_time`.
Untimed tasks (`""`) are pushed to the end with a `"99:99"` sentinel instead of
floating to the front.

### Filtering behavior — `Schedule.filter_tasks()`

Filters a task list by **completion status** (`completed=True/False`) and/or
**pet** (`pet_id=...`). Both filters are optional and composable: pass one to
narrow on it, both to narrow on both, or neither to get everything back.

### Conflict detection — `Schedule.detect_conflicts()`

Lightweight, exact-slot strategy: buckets tasks by their `"HH:MM"` time and
returns a warning string for any slot holding more than one task — whether the
tasks belong to the same pet or different pets. It never raises; a clean
schedule returns an empty list. Pass an optional `{pet_id: name}` map for
friendly names in the message (e.g. `[!] Conflict at 18:00: Evening feeding
(Rex), Play / enrichment (Luna)`). See `reflection.md` §2b for the
exact-match-vs-overlapping-durations tradeoff.

### Recurring task logic — `Pet.complete_task()` + `Task.next_occurrence()`

A `Task` carries a `frequency` (`"once"` / `"daily"` / `"weekly"`) and a
`due_date`. When `Pet.complete_task()` marks a recurring task done, it calls
`Task.next_occurrence()`, which uses `datetime.timedelta` to advance the due
date (+1 day for daily, +7 for weekly, rolling over month/year boundaries) and
returns a fresh, uncompleted copy. That copy is appended to the pet's task
list, so completing today's walk automatically queues tomorrow's. One-off
tasks return `None` and nothing is queued.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
