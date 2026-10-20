# AI Interactions Log

## Agent Workflow (SF7)

### Goal

Build PawPal+ from a four-class UML design into a working multi-pet care planner, with a CLI demo, Streamlit interface, scheduling algorithms, persistence, and automated tests. Keep the implementation modular and save meaningful Git checkpoints along the way.

### Workflow

| Phase | Files | Result |
| --- | --- | --- |
| Design | `diagrams/uml_draft.mmd`, `pawpal_system.py` | Defined Owner, Pet, Task, and Scheduler, with relationships and method interfaces. |
| Core logic | `pawpal_system.py`, `main.py` | Added multi-pet task management, completion, sorting, filtering, and a readable CLI demonstration. |
| Scheduling | `pawpal_system.py`, `tests/test_pawpal.py` | Added recurring tasks, interval conflicts, priority ordering, and next-available-slot planning. |
| Persistence | `pawpal_system.py`, `app.py` | Added versioned JSON backups that preserve tasks, history, dates, IDs, and preferences. |
| Interface | `app.py`, `.streamlit/config.toml` | Connected the domain model to forms, filters, task editing, completion controls, warnings, and explained plans. |
| Verification | `tests/test_pawpal.py`, `tests/test_app.py`, `.github/workflows/tests.yml` | Added backend and interface regression tests and GitHub checks. |
| Documentation | `README.md`, `reflection.md`, `diagrams/uml_final.mmd` | Documented the final architecture, algorithms, setup, demo output, and tradeoffs. |

### Useful refinements

- Use stable IDs rather than task descriptions to identify occurrences.
- Check overlapping date/time intervals instead of matching clock-time strings.
- Anchor recurring tasks to their due dates and make completion idempotent.
- Validate edits before replacing the original task.
- Generate suggested plans without mutating saved task times.
- Require confirmation before replacing a household during backup restoration or sample loading.

### Verification

The CLI demonstrates tasks across two pets, chronological sorting, conflict warnings, priority time blocking, and daily recurrence. The automated suite contains 41 passing tests, including real Streamlit form interactions and reruns. GitHub checks pass on Python 3.11 and 3.12. A browser walkthrough also verified downloading and restoring the sample household backup.

The remaining limitations are explicit: one caregiver, local calendar times, a greedy planner, and session-based UI storage with downloadable backups. Those boundaries keep the project understandable while leaving clear opportunities for improvement.
