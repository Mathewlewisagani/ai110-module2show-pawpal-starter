# AI Interactions Log

## Agent Workflow (Challenge 1 / SF7)

### What I asked the agent to do

Implement an additional scheduling algorithm that finds the next available time slot for a task. Use it to build an explained, priority-based care plan across multiple pets, respecting the owner's care window and task durations. Keep the backend independent of Streamlit and verify the algorithm with automated tests and a CLI example.

### Which files were modified

| File | Changes |
| --- | --- |
| `pawpal_system.py` | Added `Scheduler.next_available_slot()` and `build_plan()`, priority ordering, and `Owner.save_to_json()` / `load_from_json()`. |
| `main.py` | Added readable chronological, priority-sorted, and conflict-free plan examples. |
| `app.py` | Connected the planner to the UI; added automatic local `data.json` persistence and backup controls. |
| `tests/test_pawpal.py` | Added slot-fitting, priority, window-boundary, recurrence, conflict, and JSON tests. |
| `tests/test_app.py` | Checked UI actions and household restoration across fresh application sessions. |
| `diagrams/uml_final.mmd` | Updated the final class diagram with the scheduling and persistence methods. |
| `README.md` | Documented the algorithms, persistence workflow, output formatting, CLI examples, and verification. |

### What the agent completed

`next_available_slot()` scans occupied time intervals and returns the earliest gap large enough for a task. `build_plan()` uses that capability to assign pending due/overdue tasks in priority order, produce a chronological non-overlapping plan, and explain deferred tasks. It works across every pet through `Owner.get_all_tasks()` and does not mutate the saved requested times.

The implementation also includes an interactive Streamlit interface, automatic local JSON storage, and a CLI demo. Automated checks cover partially overlapping occupied intervals, usable gaps, exact fits, insufficient space, overdue tasks, and priority competition.

### Manual corrections and refinements

No manual code corrections were needed for the two recurrence responses below to pass the comparison tests. The challenge review did identify two project refinements: a downloadable backup alone did not demonstrate automatic persistence between runs, and the CLI needed an explicit priority-sorted example. The app now saves changes to `data.json` and reloads that file on startup; the demo now prints `Scheduler.sort_by_priority()` directly. Documentation was also reorganized to answer each challenge explicitly.

## Prompt Comparison (Challenge 5)

### Models and task

Two different models received the same task independently through Codex: **GPT-6 Sol (`gpt-6-sol`)** and **GPT-6.1 Sol (`gpt-6.1-sol`)**. The task was chosen because recurrence needs to preserve history while correctly handling dates, repeated completion, and errors.

### Shared prompt

> Implement `complete_recurring(task)`, where task is a dataclass with id, description, due_date, time, duration_minutes, priority, frequency (`once`, `daily`, or `weekly`), and completed status. Complete an occurrence once; daily creates a new incomplete occurrence one calendar day after the original due date, weekly seven days after it, and once creates none. Preserve the other care details, generate a fresh UUID, and return the successor or None. A repeated completion must not create another occurrence. If calculating the next date fails, do not partly complete the original. Do not use today's date. Provide a standalone function, reasoning, and limitations.

### Response comparison

| Question | Option A: GPT-6 Sol | Option B: GPT-6.1 Sol |
| --- | --- | --- |
| Model/tool used | `gpt-6-sol` through Codex | `gpt-6.1-sol` through Codex |
| Prompt/task | Shared recurrence prompt above | Same prompt, independently supplied |
| Response | Uses a dictionary `.get()` lookup to map daily/weekly to 1/7 days, then constructs the successor before completing the original. | Uses an explicit dictionary membership check, then constructs the successor before completing the original. |
| What was useful | Concise branches, `dataclasses.replace()` preserves care details, fresh UUID, due-date anchoring, and an early return for repeated completion. | Explicit invalid-frequency handling, a clear prepare-before-mutate sequence, preserved fields, and detailed limits around saving and concurrency. |
| What was flawed or limited | No correctness failure was found in the tested cases. It assumes a mutable dataclass and does not coordinate simultaneous completion requests. | No correctness failure was found in the tested cases. It also requires a mutable dataclass; it returns a successor without attaching or persisting it and needs transaction/locking support for concurrent use. |
| Verification | Passed the same six cases as Option B. | Passed the same six cases as Option A. |
| Final decision | A valid, slightly shorter alternative. | Selected its explicit validation and prepare-before-mutate structure for `Task.mark_complete()`. `Scheduler.mark_task_complete()` attaches the successor to the pet, and the UI saves the updated owner. |

### Evidence and final choice

The returned functions are preserved in [`comparisons/recurrence_model_a.py`](comparisons/recurrence_model_a.py) and [`comparisons/recurrence_model_b.py`](comparisons/recurrence_model_b.py). The shared tests are in [`tests/test_recurrence_comparison.py`](tests/test_recurrence_comparison.py).

Each model passes six cases: daily recurrence, weekly recurrence, one-time completion, leap-day handling, date overflow without partial mutation, and rejection of an invalid frequency. The daily/weekly cases also check metadata preservation, fresh identity, and duplicate-completion protection. Run them with:

```bash
python -m pytest tests/test_recurrence_comparison.py -v
```

Option B was adapted into the existing `Task.mark_complete()` method. Its explicit validation is easy to explain and keeps state changes after successor construction. The two solutions are largely equivalent; the final choice is based on readability and a useful explanation of limitations, rather than an invented performance difference.
