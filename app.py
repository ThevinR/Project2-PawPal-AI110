import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ is a pet care planning assistant. Add your pets and their care tasks,
and it builds a daily plan that fits your available time and explains its choices.
"""
)

st.divider()

# Streamlit reruns this script on every interaction, so the Owner lives in
# session_state and is only created the first time.
# Objects saved by an older version of the code can lack newer fields (like
# Task.due_date), so rebuild the Owner if any saved task looks stale.
if "owner" in st.session_state and any(
    not hasattr(t, "due_date") for t in st.session_state.owner.get_all_tasks()
):
    del st.session_state["owner"]
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Available time today (minutes)",
            min_value=1,
            max_value=1440,
            value=owner.available_minutes,
        )
    )

st.subheader("Pets")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    st.write("")
    st.write("")
    add_pet = st.button("Add pet")

if add_pet:
    if not new_pet_name.strip():
        st.error("Give the pet a name.")
    elif any(p.name == new_pet_name.strip() for p in owner.pets):
        st.warning(f"{new_pet_name.strip()} is already added.")
    else:
        owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species))

if owner.pets:
    st.write(", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
if owner.pets:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
    with col2:
        task_title = st.text_input("Task title", value="Morning walk")
    with col3:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        pet = next(p for p in owner.pets if p.name == task_pet)
        pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=Priority[priority.upper()],
            )
        )
else:
    st.caption("Add a pet before adding tasks.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.table(
        [
            {
                "Pet": t.pet_name,
                "Task": t.title,
                "Minutes": t.duration_minutes,
                "Priority": t.priority.name.lower(),
            }
            for t in all_tasks
        ]
    )
else:
    st.info("No tasks yet.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not all_tasks:
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        if plan:
            st.success(f"Planned {len(plan)} task(s) for {owner.name}.")
            st.table(
                [
                    {
                        "Pet": t.pet_name,
                        "Task": t.title,
                        "Minutes": t.duration_minutes,
                        "Priority": t.priority.name.lower(),
                    }
                    for t in plan
                ]
            )
        else:
            st.warning("Nothing fits in the available time.")
        st.text(scheduler.explain_plan())
