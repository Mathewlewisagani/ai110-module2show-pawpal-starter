"""Drive Streamlit forms and reruns against the real domain objects."""
from datetime import date
import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def saved_household(tmp_path, monkeypatch):
    """Keep UI tests independent from the real local household file."""
    path = tmp_path / "data.json"
    monkeypatch.setenv("PAWPAL_DATA_FILE", str(path))
    return path


def app():
    return AppTest.from_file(str(APP), default_timeout=15).run()


def button(at, label):
    return next(element for element in at.button if element.label == label)


def field(elements, label):
    return next(element for element in elements if element.label == label)


def test_empty_household_and_invalid_pet():
    at = app()
    assert not at.exception
    button(at, "Add pet").click().run()
    assert any("Pet name must not be empty" in error.value for error in at.error)
    assert len(at.session_state.owner.pets) == 0


def test_add_pet_task_edit_complete_and_retention_across_reruns():
    at = app()
    field(at.text_input, "Pet name").set_value("Mochi")
    button(at, "Add pet").click().run()
    assert len(at.session_state.owner.pets) == 1
    at.text_input(key="add_description").set_value("Breakfast")
    at.selectbox(key="add_frequency").set_value("daily")
    button(at, "Add task").click().run()
    task = at.session_state.owner.pets[0].tasks[0]
    assert task.description == "Breakfast"
    at.text_input(key=f"edit_{task.id}_description").set_value("Morning meal")
    button(at, "Save task changes").click().run()
    assert at.session_state.owner.pets[0].tasks[0].description == "Morning meal"
    button(at, "Complete").click().run()
    tasks = at.session_state.owner.pets[0].tasks
    assert len(tasks) == 2 and tasks[0].completed and not tasks[1].completed
    at.run()
    assert len(at.session_state.owner.pets[0].tasks) == 2
    assert not at.exception


def test_sample_conflicts_plan_filters_and_preferences():
    at = app()
    button(at, "Load sample household").click().run()
    assert len(at.session_state.owner.pets) == 2
    assert any("overlaps" in warning.value for warning in at.warning)
    field(at.selectbox, "Show pet").set_value("Biscuit").run()
    assert len([item for item in at.button if item.label == "Complete"]) == 2
    button(at, "Generate priority plan").click().run()
    assert any("Deferred" in warning.value for warning in at.warning)
    field(at.text_input, "Owner name").set_value("Alex")
    button(at, "Save preferences").click().run()
    assert at.session_state.owner.name == "Alex"
    assert len(at.session_state.owner.pets) == 2
    assert not at.exception


def test_sample_requires_confirmation_before_replacing_existing_household():
    at = app()
    button(at, "Load sample household").click().run()
    at.session_state.owner.name = "Keep me"
    button(at, "Load sample household").click().run()
    assert at.session_state.owner.name == "Keep me"
    button(at, "Keep my household").click().run()
    assert at.session_state.owner.name == "Keep me"
    assert not at.exception


def test_household_persists_across_fresh_app_sessions(saved_household):
    from pawpal_system import Owner
    at = app()
    button(at, "Load sample household").click().run()
    assert saved_household.exists()
    saved = Owner.load_from_json(saved_household)
    fresh = app()
    assert not fresh.exception
    assert fresh.session_state.owner == saved
    assert len(fresh.session_state.owner.pets) == 2
    assert len(fresh.session_state.owner.get_all_tasks()) == 4
    task = fresh.session_state.owner.pets[0].tasks[1]
    fresh.button(key=f"complete_{task.id}").click().run()
    restored = app()
    assert len(restored.session_state.owner.get_all_tasks()) == 5
    assert restored.session_state.owner.pets[0].tasks[1].completed


def test_invalid_saved_file_is_not_overwritten(saved_household):
    saved_household.write_text("broken data")
    at = app()
    assert any("Could not load" in error.value for error in at.error)
    assert saved_household.read_text() == "broken data"


def test_save_failure_is_visible_without_false_success(saved_household):
    at = app()
    saved_household.mkdir()
    field(at.text_input, "Owner name").set_value("Alex")
    button(at, "Save preferences").click().run()
    assert any("could not be saved" in error.value for error in at.error)
    assert not any("preferences saved" in item.value for item in at.success)
