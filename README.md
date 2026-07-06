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

## ✨ Features

PawPal+ pairs an interactive Streamlit UI with a tested Python logic layer
(`pawpal_system.py`). The scheduling algorithms it implements:

- **Sorting by time** — orders tasks chronologically by their `"HH:MM"` slot;
  untimed tasks sort to the *end*, not the front (`Schedule.sort_by_time`).
- **Filtering** — narrows a task list by completion status and/or pet, and the
  two filters compose (`Schedule.filter_tasks`).
- **Conflict warnings** — flags any two tasks booked in the same time slot,
  naming the pets involved so the owner knows what to move
  (`Schedule.detect_conflicts`).
- **Daily / weekly recurrence** — completing a recurring task auto-queues its
  next occurrence (+1 day or +7 days), rolling across month and year boundaries
  (`Pet.complete_task` + `Task.next_occurrence`).
- **Priority-ordered daily plan** — builds the day's plan sorted by priority
  (highest first), then by time (`Owner.get_daily_plan` →
  `Schedule.generate_daily_plan`).

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

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite lives in [`tests/test_pawpal.py`](tests/test_pawpal.py) and has **11 tests**
across the core scheduling behaviors, mixing happy paths with edge cases:

- **Basics** — completing a task flips its status; adding a task grows the pet's list.
- **Sorting** — tasks are returned in chronological `"HH:MM"` order, and untimed
  tasks (`""`) sort to the *end*, not the front.
- **Recurrence** — completing a `daily` task queues a fresh copy due +1 day; a
  `weekly` task advances +7 days (rolling across month boundaries); a one-off
  task creates no follow-up.
- **Conflict detection** — two tasks in the same time slot produce exactly one
  warning; a clean schedule returns an empty list; untimed tasks are ignored.
- **Edge case** — an owner whose pet has no tasks gets an empty daily plan
  instead of a crash.

### Successful test run

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\onlyj\AppData\Local\Python\pythoncore-3.14-64\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\onlyj\Documents\Engineering Stuff\Code Path\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collecting ... collected 11 items

tests/test_pawpal.py::test_mark_completed_changes_status PASSED          [  9%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 18%]
tests/test_pawpal.py::test_sort_by_time_orders_chronologically PASSED    [ 27%]
tests/test_pawpal.py::test_sort_by_time_pushes_untimed_tasks_to_end PASSED [ 36%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day_task PASSED [ 45%]
tests/test_pawpal.py::test_weekly_task_advances_seven_days PASSED        [ 54%]
tests/test_pawpal.py::test_completing_one_off_task_creates_no_follow_up PASSED [ 63%]
tests/test_pawpal.py::test_detect_conflicts_flags_two_tasks_at_same_time PASSED [ 72%]
tests/test_pawpal.py::test_detect_conflicts_clean_schedule_returns_empty PASSED [ 81%]
tests/test_pawpal.py::test_detect_conflicts_ignores_untimed_tasks PASSED [ 90%]
tests/test_pawpal.py::test_daily_plan_for_owner_with_no_tasks_is_empty PASSED [100%]

============================= 11 passed in 0.05s ==============================
```

### Confidence Level: ★★★★☆ (4/5)

All 11 tests pass and cover every core scheduling behavior — sorting,
recurrence, filtering, and conflict detection — including edge cases like
untimed tasks, one-off completion, and empty pets. I'm holding back the fifth
star because a couple of known gaps remain untested: `generate_daily_plan`
places untimed tasks at the *front* (opposite of `sort_by_time`), and conflict
detection only catches exact-time collisions, not overlapping durations. The
logic is reliable for the behaviors verified; the missing star reflects
coverage breadth, not observed defects.

## 📐 Smarter Scheduling

These are the algorithmic features added on top of the base logic layer. Each
method lives in `pawpal_system.py` and is exercised by `main.py` and the tests
in `tests/test_pawpal.py`.

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

## 🎬 Demo Walkthrough

PawPal+ has two faces that share the same logic layer: an interactive
**Streamlit app** (`app.py`) for everyday use, and a **command-line demo**
(`main.py`) that exercises the scheduling algorithms in one run.

### The Streamlit app — `streamlit run app.py`

The UI is organized top-to-bottom into sections. Every action calls a real
method on the persisted `Owner` / `Pet` / `Schedule` objects (state survives
Streamlit's reruns via `st.session_state`):

- **Owner** — set the owner's name.
- **Add a Pet** — submit a name, species, and age → `Owner.add_pet()`.
- **Schedule a Task** — pick a pet, then enter a task title, duration, priority,
  and time slot → `Pet.add_task()` and (if timed) `Schedule.add_task()`.
- **Task list** — a per-pet table with a **Show** filter (All / Pending /
  Completed) and a **Sort by time** toggle, driven by `Schedule.filter_tasks()`
  and `Schedule.sort_by_time()`.
- **Build Schedule** — generates the day's priority-ordered plan
  (`Owner.get_daily_plan()`) and surfaces any **conflict warnings**
  (`Schedule.detect_conflicts()`) as a yellow `st.warning` callout that names the
  clashing tasks and pets.

### Example workflow

1. Enter the owner name (e.g. *Alex*).
2. **Add a pet** — *Rex, dog, age 3*.
3. **Schedule a task** — *Morning walk*, 30 min, high priority, `08:00`.
4. Add a second pet (*Luna*) and give her a task at `18:00` — the same slot as
   one of Rex's tasks.
5. Use the **Show** / **Sort by time** controls to review each pet's tasks in
   chronological order and hide completed ones.
6. Click **Build Schedule** → the plan appears priority-first, and a **conflict
   warning** flags the `18:00` double-booking so you know to reschedule one.

### Key scheduler behaviors shown

- **Sorting** — tasks entered out of order (evening before morning) come back
  `08:00 → 18:00`.
- **Filtering** — hiding completed tasks, and viewing a single pet's list.
- **Conflict warnings** — two tasks at `18:00` produce one human-readable
  warning naming both pets.
- **Recurrence** — completing the daily *Morning walk* auto-creates tomorrow's
  copy.

### Sample CLI output — `python main.py`

`main.py` builds an owner (*Alex*) with two pets and four tasks — added out of
time order, one already completed, two deliberately at the same `18:00` slot —
then demonstrates each behavior in turn:

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

*Optional:* add screenshots of the Streamlit UI here for human reviewers — the
text walkthrough and CLI output above are the gradable record.
