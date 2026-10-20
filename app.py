"""Streamlit interface; all care rules live in pawpal_system.py."""
from datetime import date, datetime
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITIES, FREQUENCIES
from main import build_demo

st.set_page_config(page_title="PawPal+ · A little care, every day", page_icon="🐾", layout="wide")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))


def refresh(message):
    """Keep an action's confirmation visible after the next Streamlit rerun."""
    st.session_state.notice = message
    st.rerun()


def task_fields(prefix, task=None):
    """Render shared creation/edit fields so both forms expose the same rules."""
    description = st.text_input("Task description", value=task.description if task else "", key=f"{prefix}_description")
    left, right = st.columns(2)
    with left:
        due = st.date_input("Due date", value=task.due_date if task else selected_day, key=f"{prefix}_date")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440,
                                   value=task.duration_minutes if task else 20, key=f"{prefix}_duration")
        frequency = st.selectbox("Repeat", list(FREQUENCIES),
                                index=list(FREQUENCIES).index(task.frequency) if task else 0, key=f"{prefix}_frequency")
    with right:
        at = st.time_input("Requested time", value=datetime.strptime(task.time if task else "08:00", "%H:%M").time(),
                           step=60, key=f"{prefix}_time")
        priority = st.selectbox("Priority", list(PRIORITIES),
                               index=list(PRIORITIES).index(task.priority) if task else 1, key=f"{prefix}_priority")
    return dict(description=description, due_date=due, time=at.strftime("%H:%M"),
                duration_minutes=int(duration), priority=priority, frequency=frequency)


owner = st.session_state.owner
scheduler = Scheduler(owner)
with st.sidebar:
    st.markdown("## 🐾 PawPal+")
    st.caption("A little care, every day.")
    selected_day = st.date_input("Schedule date", value=date.today())
    with st.form("owner_preferences"):
        st.markdown("### Your care window")
        name = st.text_input("Owner name", value=owner.name)
        start = st.time_input("Start time", value=datetime.strptime(owner.preferred_start, "%H:%M").time(), step=60)
        minutes = st.number_input("Window length (minutes)", min_value=1, max_value=1440, value=owner.available_minutes)
        if st.form_submit_button("Save preferences", use_container_width=True):
            try:
                st.session_state.owner = Owner(name, owner.pets, start.strftime("%H:%M"), int(minutes))
                refresh("Care preferences saved.")
            except ValueError as error:
                st.error(str(error))
    if st.button("Load sample household", use_container_width=True):
        if owner.pets:
            st.session_state.confirm_sample = True
        else:
            st.session_state.owner = build_demo(selected_day)
            refresh("Sample household loaded. Try generating a plan or completing Breakfast.")
    if st.session_state.get("confirm_sample"):
        st.warning("Loading the sample replaces this session's household. Export a backup first if you want to keep it.")
        if st.button("Replace with sample"):
            st.session_state.owner = build_demo(selected_day)
            st.session_state.pop("confirm_sample", None)
            refresh("Sample household loaded.")
        if st.button("Keep my household"):
            st.session_state.pop("confirm_sample", None)
            st.rerun()
    st.divider()
    st.caption("Your household stays in this browser session. Use Backup to save it between visits.")

st.title("Care for every member of the pack.")
st.write(f"{owner.name}'s household · {selected_day.strftime('%A, %B %d')}")
pending = scheduler.filter_tasks(completed=False, day=selected_day)
col1, col2, col3 = st.columns(3)
col1.metric("Pets in your care", len(owner.pets))
col2.metric("Tasks due today", len(pending))
col3.metric("Care minutes due", sum(task.duration_minutes for _, task in pending))
schedule_tab, manage_tab, backup_tab = st.tabs(["Today's care", "Pets & tasks", "Backup"])

with schedule_tab:
    st.subheader("The daily lineup")
    filters = st.columns(2)
    pet_filter = filters[0].selectbox("Show pet", ["All pets"] + [pet.name for pet in owner.pets])
    status_filter = filters[1].selectbox("Show status", ["Pending", "All tasks", "Completed"])
    completed_filter = {"Pending": False, "All tasks": None, "Completed": True}[status_filter]
    visible = scheduler.sort_by_time(selected_day, None if pet_filter == "All pets" else pet_filter, completed_filter)
    for warning in scheduler.detect_conflicts(selected_day):
        st.warning(warning)
    overdue = [(pet, task) for pet, task in scheduler.filter_tasks(completed=False) if task.due_date < selected_day]
    if overdue:
        st.warning(f"{len(overdue)} overdue task(s). The priority plan includes these too.")
    if not visible:
        st.info("No tasks match this view. Add a pet and a task, or load the sample household.")
    for pet, task in visible:
        with st.container(border=True):
            detail, action = st.columns([3, 1.2])
            with detail:
                st.markdown(f"**{task.time} · {task.description}**")
                st.caption(f"{pet.name} · {task.duration_minutes} min · {task.priority.title()} priority · {task.frequency.title()}")
                if task.completed:
                    st.success("Completed")
            with action:
                if not task.completed and st.button("Complete", key=f"complete_{task.id}", use_container_width=True):
                    try:
                        following = scheduler.mark_task_complete(task.id)
                        suffix = f" Next occurrence: {following.due_date} at {following.time}." if following else ""
                        refresh(f"Completed {task.description} for {pet.name}.{suffix}")
                    except (ValueError, OverflowError) as error:
                        st.error(f"Could not complete task: {error}")
    st.divider()
    st.subheader("Make room for what matters")
    st.caption("High priority first, then requested time. Tasks move to the first free slot; your original task times stay unchanged. Review this suggestion before acting on it.")
    if st.button("Generate priority plan", type="primary"):
        plan = scheduler.build_plan(selected_day)
        st.write(f"Care window: {plan['start']:%H:%M}–{plan['end']:%H:%M} (ends at midnight if necessary)")
        if not plan["scheduled"]:
            st.info("No pending tasks fit this window. Adjust the window or add a task.")
        for pet, task, reason in plan["scheduled"]:
            with st.container(border=True):
                st.markdown(f"**{task.time}–{task.ends_at:%H:%M} · {pet.name} · {task.description}**")
                st.caption(f"{task.duration_minutes} min · {reason}")
        for pet, task, reason in plan["deferred"]:
            st.warning(f"Deferred: {pet.name} · {task.description}. {reason}")
        st.caption("Requested times are earliest starts, not hard deadlines. The plan is a suggestion and does not reschedule your saved tasks.")

with manage_tab:
    st.subheader("Your household")
    if owner.pets:
        st.dataframe([{"Pet": pet.name, "Species": pet.species, "Care tasks": len(pet.tasks)} for pet in owner.pets],
                     hide_index=True, use_container_width=True)
    with st.expander("Add a pet", expanded=not owner.pets):
        with st.form("add_pet", clear_on_submit=True):
            pet_name = st.text_input("Pet name")
            species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
            if st.form_submit_button("Add pet"):
                try:
                    owner.add_pet(Pet(pet_name, species))
                    refresh(f"{pet_name.strip()} joined your household.")
                except ValueError as error:
                    st.error(str(error))
    if owner.pets:
        st.subheader("Schedule a care task")
        with st.form("add_task", clear_on_submit=True):
            target = st.selectbox("Pet", [pet.name for pet in owner.pets])
            values = task_fields("add")
            if st.form_submit_button("Add task", type="primary"):
                try:
                    pet = next(pet for pet in owner.pets if pet.name == target)
                    pet.add_task(Task(**values))
                    refresh(f"Task added for {target}.")
                except ValueError as error:
                    st.error(str(error))
        editable = scheduler.filter_tasks(completed=False)
        if editable:
            st.subheader("Edit a pending task")
            entries = {task.id: (pet, task) for pet, task in editable}
            selection = st.selectbox("Task to edit", list(entries),
                format_func=lambda identifier: f"{entries[identifier][0].name} · {entries[identifier][1].description} · {entries[identifier][1].due_date}")
            pet, task = entries[selection]
            with st.form(f"edit_task_{selection}"):
                changes = task_fields(f"edit_{selection}", task)
                if st.form_submit_button("Save task changes"):
                    try:
                        scheduler.update_task(selection, **changes)
                        refresh("Task updated.")
                    except ValueError as error:
                        st.error(str(error))
    else:
        st.info("Add your first pet to start scheduling care.")

with backup_tab:
    st.subheader("Keep your household close")
    st.write("Download a JSON backup to restore your pets, care history, and preferences on another visit. Nothing is uploaded to a shared household database.")
    st.download_button("Download household backup", owner.to_json(), "pawpal-household.json", "application/json")
    uploaded = st.file_uploader("Restore a PawPal JSON backup", type=["json"])
    replace_confirmed = st.checkbox("Replace my current household with this backup")
    if st.button("Restore household", disabled=uploaded is None or not replace_confirmed):
        try:
            if uploaded.size > 1_000_000:
                raise ValueError("Please choose a backup smaller than 1 MB.")
            restored = Owner.from_json(uploaded.getvalue().decode("utf-8"))
            st.session_state.owner = restored
            refresh("Household restored from backup.")
        except (ValueError, UnicodeError, RecursionError) as error:
            st.error(str(error))
