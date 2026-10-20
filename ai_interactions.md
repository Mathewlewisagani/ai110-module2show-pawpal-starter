# AI Interactions Log

## Agent Workflow (SF7)

**Task given to the agent**

The user asked: “work on this project fully pushing the changes to my github incrementally. if a repo does not exist the instructions show where to fork the repo from”. The PDF supplied the project requirements. Earlier user requests authorized cloning the starter and installing its requirements.

**Work completed by Codex**

- Read the offline brief and starter files, checked the authenticated GitHub account, created a fork under `Mathewlewisagani`, and kept the CodePath source as `upstream`.
- Drafted `diagrams/uml_draft.mmd` and class skeletons in `pawpal_system.py` as the first checkpoint.
- Implemented the four domain classes, multi-pet sorting/filtering/conflicts, completion and recurrence, plus the reproducible `main.py` demo.
- Added `Scheduler.next_available_slot()` and `build_plan()` for priority-based time blocking, with JSON backup/restore methods on `Owner`.
- Connected `app.py` to the domain model, stored the owner in `st.session_state`, and added native Streamlit forms, warnings, filters, task edits, recurrence completion, preferences, and backup controls.
- Wrote backend tests and Streamlit AppTest scenarios, ran the CLI and test suite, reviewed the actual browser interface, and added a GitHub Actions workflow.
- Updated `README.md`, `reflection.md`, `diagrams/uml_final.mmd`, the matching `diagrams/uml.mmd`, `.streamlit/config.toml`, `.gitignore`, and a dependency snapshot.

**Corrections and verification**

The first fork command included a combination of CLI options that GitHub CLI rejected. Codex corrected the command and verified that GitHub returned the new fork URL. No code defect is represented as a manual student correction. Agent design checks chose idempotent recurrence, date-aware duration conflicts, atomic edits, explicit import replacement confirmation, and non-mutating suggested plans. Tests exercise those decisions; the README records actual demo and test output.

No second AI model or separate prompt-comparison experiment was used. No SF11 model-comparison claim is made. The student has not yet provided a manual review or a personal reflection in this conversation.
