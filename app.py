import streamlit as st

# Bring the logic layer into the UI. These are the same classes defined in
# pawpal_system.py — importing them lets button clicks drive real objects.
from pawpal_system import Owner, Pet, Task, Schedule

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# The UI captures priority as a word; the Task class stores it as a number
# (higher = more important). This maps between the two worlds.
PRIORITY_TO_INT = {"low": 1, "medium": 2, "high": 3}

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# Timeslots the Schedule can place tasks into. "" means "no specific time".
TIMESLOTS = ["08:00", "12:00", "15:00", "18:00", "21:00"]

# --- Session vault -------------------------------------------------------
# Streamlit reruns this whole file top-to-bottom on every interaction. If we
# built a fresh Owner here each time, its pets and tasks would be wiped on
# every click. So we create the Owner ONCE and stash it in st.session_state
# (a dict that survives reruns). On later reruns we just fetch it back.
if "owner" not in st.session_state:
    owner = Owner(id="owner-1", name=owner_name)
    owner.schedule = Schedule(timeslots=list(TIMESLOTS))  # give it a "brain"
    st.session_state.owner = owner
    st.session_state.pet_counter = 0   # keeps pet ids unique across reruns
    st.session_state.task_counter = 0  # keeps task ids unique across reruns

# Pull the persistent object back out of the vault.
owner = st.session_state.owner
owner.name = owner_name  # keep the stored owner in sync with the input box

int_to_priority = {v: k for k, v in PRIORITY_TO_INT.items()}

st.divider()

# --- Add a Pet -----------------------------------------------------------
st.subheader("Add a Pet")
st.caption("Submitting this form calls Owner.add_pet() on your persisted owner.")

with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="Mochi")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    new_pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=3)
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    # THIS is the class method that handles the form data:
    new_pet = Pet(
        id=f"pet-{st.session_state.pet_counter}",
        name=new_pet_name,
        species=new_pet_species,
        age=int(new_pet_age),
    )
    owner.add_pet(new_pet)  # <-- Owner.add_pet appends it to owner.pets
    st.session_state.pet_counter += 1
    st.success(f"Added {new_pet.name} the {new_pet.species}.")

# Because the owner persists in the vault, this list already reflects the
# add above — Streamlit re-ran the script and re-read owner.pets for us.
if not owner.pets:
    st.info("No pets yet. Add one above to get started.")
    st.stop()

st.write(f"{owner.name} has {len(owner.pets)} pet(s): "
         + ", ".join(p.name for p in owner.pets))

st.divider()

# --- Schedule a Task for a Pet -------------------------------------------
st.subheader("Schedule a Task")

# Pick which persisted pet to attach the task to.
pet = st.selectbox(
    "Pet",
    options=owner.pets,
    format_func=lambda p: f"{p.name} ({p.species})",
)

with st.form("add_task_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    time_choice = st.selectbox("Time slot", ["(no time)"] + TIMESLOTS)
    submitted_task = st.form_submit_button("Schedule task")

if submitted_task:
    task = Task(
        id=f"task-{st.session_state.task_counter}",
        pet_id=pet.id,
        type=task_title,
        duration_minutes=int(duration),
        priority=PRIORITY_TO_INT.get(priority, 1),
    )
    pet.add_task(task)  # <-- Pet.add_task attaches it to this pet
    if time_choice != "(no time)":
        # Schedule.add_task places it in a timeslot AND sets its time.
        owner.schedule.add_task(task, time_choice)
    st.session_state.task_counter += 1
    st.success(f"Scheduled '{task.type}' for {pet.name}.")

if pet.tasks:
    st.write(f"Tasks for {pet.name}:")
    st.table(
        [
            {
                "task": t.type,
                "time": t.scheduled_time or "—",
                "duration (min)": t.duration_minutes,
                "priority": int_to_priority.get(t.priority, t.priority),
                "done": t.completed,
            }
            for t in pet.tasks
        ]
    )
else:
    st.info(f"{pet.name} has no tasks yet.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button calls Owner.get_daily_plan() on the persisted owner.")

if st.button("Generate schedule"):
    plan = owner.get_daily_plan(date="today")
    if not plan:
        st.info("No pending tasks to plan. Schedule a task above first.")
    else:
        st.success(f"Built a plan with {len(plan)} task(s) for {owner.name}.")
        st.write("Ordered plan (highest priority first, then by time):")
        st.table(
            [
                {
                    "order": order,
                    "pet": next(p.name for p in owner.pets if p.id == task.pet_id),
                    "task": task.type,
                    "time": task.scheduled_time or "—",
                    "duration (min)": task.duration_minutes,
                    "priority": int_to_priority.get(task.priority, task.priority),
                }
                for order, task in enumerate(plan, start=1)
            ]
        )
