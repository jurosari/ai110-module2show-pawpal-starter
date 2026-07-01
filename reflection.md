# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Core actions (user-facing):
    - Track pet care tasks (create, update, complete tasks for pets).
    - Owner schedule preference (set availability and preferred times).
    - Produce daily plan (generate a consolidated list of tasks for today).

- High-level UML overview:
    - Classes: `Owner`, `Pet`, `Task`, `Schedule`.
    - Relationships: an `Owner` owns one or more `Pet` objects; each `Pet` has zero or more `Task` items; an `Owner` is associated with a `Schedule` that organizes `Task` items into timeslots.

- Classes chosen and their responsibilities:
    - `Owner` — Top-level entity representing the human user. Holds identity (`id`, `name`), `availability`, `preferences`, and the list of `pets` they manage. Responsible for setting availability, adding/removing pets, updating preferences, and requesting a daily plan.
    - `Pet` — Holds pet details (`id`, `name`, `species`, `age`) and the list of `tasks` specific to that pet. Responsible for adding/removing its own tasks, reporting pending tasks, and updating its info. Each `Task` belongs to exactly one `Pet`.
    - `Task` — The core unit of work: a single care action (walk, feed, meds, groom, enrich). Holds scheduling info (`scheduled_time`, `duration_minutes`), `completed` state, and `priority`. Responsible for scheduling/rescheduling itself, marking completion, and setting its priority.
    - `Schedule` — The planning engine. Knows the `days_of_week`, available `timeslots`, and a `slots` map of assigned tasks. Responsible for placing/removing/editing tasks in time, finding an available slot for a given duration and preferences, and generating the consolidated daily plan across all of an owner's pets.

- Building blocks:
    - `Owner`: attributes `id`, `name`, `availability` (days -> timeslots), `pets` (list of `Pet`), `preferences`; methods `set_availability`, `add_pet`, `remove_pet`, `update_preferences`, `get_daily_plan`.
    - `Pet`: attributes `id`, `name`, `species`, `age`, `tasks` (list of `Task`); methods `add_task`, `remove_task`, `get_pending_tasks`, `update_info`.
    - `Task`: attributes `id`, `pet_id`, `type`, `scheduled_time`, `duration_minutes`, `completed`, `priority`; methods `schedule`, `reschedule`, `mark_completed`, `set_priority`.
    - `Schedule`: attributes `days_of_week`, `timeslots`, `slots`; methods `add_task`, `remove_task`, `edit_task`, `find_available_slot`, `generate_daily_plan`.

- Mapping to core actions:
    - Track pet care tasks: `Pet.add_task`, `Task.mark_completed`, `Schedule.generate_daily_plan`.
    - Owner schedule preference: `Owner.set_availability`, `Schedule.find_available_slot`.
    - Produce daily plan: `Schedule.generate_daily_plan`, `Owner.get_daily_plan`.

**b. Design changes**

I asked my AI coding assistant to review the `pawpal_system.py` skeleton for missing relationships and potential logic bottlenecks. Two findings:

- **Missing relationship: `Owner` → `Schedule`.** The UML declares `Owner "1" --> "1" Schedule : uses`, but the `Owner` dataclass had no reference to a `Schedule`. Without it, `Owner.get_daily_plan(date)` has nothing to delegate to. I recorded the proposed fix (a `schedule: Schedule | None = None` field on `Owner`) as a comment in the code so the relationship is visible, rather than silently leaving the gap. This keeps the code honest to the UML.

- **Potential bottleneck: task lookup by id.** Tasks are stored in each `Pet.tasks` list and also referenced from `Schedule.slots`, with no central index. As a result `Schedule.remove_task`/`edit_task` must linear-scan every slot, and `generate_daily_plan` must traverse `owner.pets[*].tasks` on every call. For the expected scale (a handful of pets and tasks per day) this is acceptable, so I kept the simpler design and noted it here as a known tradeoff rather than adding an index prematurely.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- **The tradeoff: `detect_conflicts` flags only exact start-time matches, not overlapping durations.** It buckets tasks by their `"HH:MM"` slot and warns when a slot holds more than one task. So an 08:00 walk lasting 30 minutes and an 08:15 feeding are *not* flagged, even though they physically overlap — because their start strings differ. A true overlap check would need each task's end time (start + `duration_minutes`) and an interval sweep.

- **Why it's reasonable here.** PawPal+ places tasks into a small set of discrete, owner-defined timeslots (e.g. 08:00 / 12:00 / 18:00), so in practice conflicts show up as two tasks landing in the *same* slot — exactly what the exact-match check catches. The lightweight version is O(n) with a single dict, returns plain warning strings (never raises), and is easy for a human to read and trust. Full interval-overlap detection adds an `end_time()` concept and time-arithmetic that isn't justified until tasks can be scheduled at arbitrary minutes rather than fixed slots. I noted it as a known limitation so the upgrade path (`Task.end_time()` + a sorted sweep) is explicit rather than forgotten.

- **Aside — a readability-vs-idiom call I made while writing it.** I asked my AI assistant how to simplify the bucketing loop. Its more "Pythonic" suggestion used `itertools.groupby` (sort tasks by time, then group). I kept my explicit `dict.setdefault` loop instead: `groupby` requires the input to be pre-sorted and silently returns wrong groups if it isn't — a subtle trap — whereas the plain dict loop reads top-to-bottom with no hidden precondition. Here I judged the clearer, harder-to-misuse version worth more than the idiomatic one-liner.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
