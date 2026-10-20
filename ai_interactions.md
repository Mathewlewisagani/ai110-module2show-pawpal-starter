# AI Interactions Log

## Agent Workflow (Challenge 1)

### What I asked the agent to do

Add a next-available-slot algorithm and use it to build a priority-based plan across multiple pets. The plan should fit inside the owner's care window, avoid overlaps, and show tasks that do not fit.

### Files modified

- `pawpal_system.py`: slot finding, planning, priority sorting, and JSON save/load.
- `main.py`: CLI examples for sorting, filtering, conflicts, and planning.
- `app.py`: UI controls, automatic `data.json` storage, and backups.
- `tests/test_pawpal.py` and `tests/test_app.py`: backend and UI tests.
- `diagrams/uml_final.mmd`: updated classes and methods.
- `README.md`: setup, examples, algorithms, and test results.

### What it completed

`next_available_slot()` finds the first gap large enough for a task. `build_plan()` uses it to place high-priority tasks first and lists tasks that cannot fit. It gets tasks from all pets through `Owner.get_all_tasks()`. It does not change their saved requested times.

### Corrections made

The first version had downloadable backups but did not automatically reload saved data. It now saves changes to `data.json` and loads the file when the app starts. The CLI example was also changed so a later high-priority task appears before an earlier low-priority task.

No manual changes were needed for the two recurrence responses below to pass their comparison tests.

## Prompt Comparison (Challenge 5)

### Task and prompt

Both models received the same task independently:

> Write `complete_recurring(task)` for a Task dataclass. Daily tasks should create a new occurrence one day after the original due date, weekly tasks seven days after it, and one-time tasks should not repeat. Keep the other details, give the new task a fresh ID, and leave it incomplete. Completing the original twice must not create another task. If calculating the next date fails, leave the original incomplete. Do not use today's date. Explain the code and its limits.

### Comparison

| Question | Model A | Model B |
| --- | --- | --- |
| Model/tool | GPT-6 Sol (`gpt-6-sol`) through Codex | GPT-6.1 Sol (`gpt-6.1-sol`) through Codex |
| Approach | Looks up the repeat interval with `.get()`, creates the next task, then completes the original. | Checks the frequency explicitly, creates the next task, then completes the original. |
| Useful parts | Short code, preserved task details, fresh ID, and protection against repeated completion. | Clear validation and order of operations. Also explains that saving and concurrent requests need separate handling. |
| Problems or limits | Passed the tests. Assumes a mutable dataclass and does not handle simultaneous completion requests. | Also passed. Returns the next task but does not attach or save it, and does not handle simultaneous requests. |
| Test result | Passed all six comparison cases. | Passed all six comparison cases. |

### Final decision

I chose Model B's explicit checks for `Task.mark_complete()` because they are easier to follow. `Scheduler.mark_task_complete()` adds the returned task to the pet, and the app saves the household. The two answers behave much the same; the choice was about readability.

The returned code is saved in `comparisons/recurrence_model_a.py` and `comparisons/recurrence_model_b.py`. The shared tests check daily and weekly recurrence, one-time tasks, leap day, date overflow, and invalid frequency. They also check new IDs, preserved details, and duplicate completion.

```bash
python -m pytest tests/test_recurrence_comparison.py -v
```

Result: 12 passing checks, six per model.
