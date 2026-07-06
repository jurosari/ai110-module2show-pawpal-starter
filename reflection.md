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

**a. How you used AI (which features were most effective)**

I used my AI coding assistant across every phase — design brainstorming, code
review, test generation, refactoring, and docs — but a few specific features
did the most work for building the scheduler:

- **Codebase-aware design review.** The single most effective feature was
  handing the assistant my `pawpal_system.py` skeleton and asking it to audit
  the code *against my UML* for missing relationships and bottlenecks. This is
  what surfaced the missing `Owner → Schedule` reference (§1b): the UML declared
  the relationship but the dataclass had no `schedule` field, so
  `get_daily_plan` had nothing to delegate to. A review that reads the whole
  file at once caught a structural gap I would have hit only at runtime.
- **Diff review as a safety net.** When a later edit silently dropped
  `detect_conflicts` from the file, running the tests and asking the assistant
  to reconcile the failing suite against the code immediately located the
  regression — the tests, `main.py`, and README all referenced a method that no
  longer existed. Treating the test suite as the source of truth and letting AI
  chase the diff was far faster than hunting by hand.
- **Test scaffolding for edge cases.** Asking specifically for *edge-case* tests
  (not just happy paths) produced the untimed-tasks-sort-last case, the one-off
  task that must **not** spawn a follow-up, and the empty-pet daily plan. These
  named the behaviors I actually cared about and became the spec I held later
  changes to.
- **"What are the tradeoffs of X" prompts.** The most helpful *kind* of prompt
  was never "write me X" — it was "here's my approach to X, what breaks?" That
  framing turned the assistant into a critic and produced the conflict-detection
  limitation analysis (exact-slot vs. interval overlap, §2b) rather than a wall
  of code I'd have to reverse-engineer.

**b. Judgment and verification (a suggestion I rejected/modified)**

The clearest example is documented in §2b: for the conflict-detection bucketing
loop, the assistant suggested a more "Pythonic" `itertools.groupby` one-liner. I
**rejected** it and kept my explicit `dict.setdefault` loop. `groupby` only
groups *adjacent* equal keys, so it silently returns wrong groups unless the
input is pre-sorted — a hidden precondition that would have produced
missed-conflict bugs the moment tasks arrived unsorted (which, in `main.py`,
they deliberately do). The plain dict loop has no such trap and reads
top-to-bottom. I judged "harder to misuse" as worth more than "fewer lines."

A second, smaller modification: when wiring conflict warnings into the Streamlit
UI, the raw backend string carried a `[!]` prefix meant for the terminal. Rather
than change the backend contract (which `main.py` and the tests depend on), I
stripped the prefix at the UI layer so each surface presents the same data in
its own idiom. Same data, right presentation per medium.

How I verified suggestions: I never accepted code because it *sounded* right. I
ran `python -m pytest` after every logic change (11 tests, all passing), ran
`python main.py` to see real output rather than trusting a described output, and
checked each suggestion against my UML and the tests-as-spec. When AI output and
the tests disagreed, the tests won.

**c. How separate chat sessions per phase kept me organized**

I ran a distinct session per phase — UML design, logic implementation, the
"smarter scheduling" features, the Streamlit UI, and docs/reflection — rather
than one sprawling thread. This helped in three concrete ways:

- **Focused context.** Each session only carried the files and decisions
  relevant to that phase, so suggestions stayed on-topic instead of the
  assistant re-litigating settled design choices or "helpfully" rewriting
  already-stable code from an earlier phase.
- **Traceable decisions.** One phase per session made it easy to go back and
  find *why* a choice was made — the conflict-detection tradeoff lives with the
  Phase 3 work, not buried in a 500-message thread.
- **Clean checkpoints.** Finishing a phase, committing, and starting a fresh
  session forced me to treat each layer's output as a stable contract before
  building the next layer on top of it — the same discipline the UML → stubs →
  logic → UI ordering encourages.

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

**c. Key takeaway — being the "lead architect" with powerful AI tools**

The biggest thing I learned is that a powerful AI assistant changes *what* I do,
not *who owns the design*. It's a fast, tireless implementer and an excellent
critic — but it will confidently generate fluent code for the wrong design just
as readily as the right one, so it can't be the one deciding what "right" means.

Being lead architect came down to owning three things the AI could not:

- **The invariants and contracts.** The UML and, especially, the test suite were
  *my* specification of correct behavior. Every AI suggestion was measured
  against them, and when they disagreed, the spec won. Writing the tests and the
  class contracts first is what let me delegate implementation without losing
  control of correctness.
- **The "why," not just the "how."** The AI is strongest at "how do I do X"
  and weakest at "*should* I do X here." The valuable judgment calls — keeping
  the exact-slot conflict check instead of premature interval logic, rejecting
  `groupby` for a loop that can't be misused, not adding a task index the scale
  doesn't justify — were all decisions to keep the design simple and honest, and
  those stayed mine.
- **Verification over trust.** Fluent output is not correct output. Running the
  tests and `main.py` on every change, rather than accepting described results,
  is what caught a silently dropped method and kept the code honest to its docs.

In short: the AI made me faster at the mechanical work and sharper through
review, but the architecture, the constraints, and the accountability for
verifying the result had to stay with me. Delegating the typing is fine;
delegating the judgment is not.
