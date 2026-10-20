# PawPal+ Project Reflection

## 1. System Design

### a. Initial design

My goal for PawPal+ was to make three actions straightforward: add a pet, schedule care, and check what needs to happen today. The design separates those responsibilities into four classes. `Owner` manages the household, `Pet` holds its tasks, `Task` describes one care activity, and `Scheduler` organizes tasks across all pets. Dataclasses keep the model readable without a lot of repeated initialization code.

### b. Design changes

The final design adds stable task IDs, owner preferences, and JSON persistence. Task IDs matter because different pets can have tasks with the same name. The scheduler also uses both dates and durations, rather than comparing clock times alone. Another useful change is keeping generated plans separate from saved tasks: trying a different care window produces a suggestion without overwriting the original schedule.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

The scheduler considers each task's date, requested time, duration, priority, and completion status, along with the owner's available care window. High-priority tasks get the first available slots, with due time breaking ties. Completed and future tasks stay out of the plan, while overdue tasks remain visible. The result is displayed chronologically, with an explanation for each scheduled task and a separate list of tasks that do not fit.

### b. Tradeoffs

My scheduler favors a simple greedy approach over finding a mathematically optimal plan. A long high-priority task can take time that several shorter tasks could have used. That is reasonable for a small pet-care planner because the behavior is easy to understand and explain.

Requested times are treated as earliest starts, not strict deadlines. Conflict detection assumes one caregiver and checks overlapping time intervals across pets. Two activities that touch at their endpoints are allowed. The app does not yet account for travel time, multiple caregivers, or time zones.

## 3. AI Collaboration

### a. How AI was used

AI assistance was useful for translating the UML into dataclasses, scaffolding methods, suggesting edge cases, and connecting the backend to Streamlit. The most useful context was specific: the four required classes, the multi-pet requirement, the recurrence rules, and the expected CLI output.

The work was organized into design, core implementation, scheduling algorithms, UI integration, and verification checkpoints. Keeping those phases separate made it easier to check the logic before adding interface behavior. The same conversation was used throughout, with incremental commits preserving each stage.

### b. Judgment and verification

One important refinement was moving beyond a same-time conflict check. Comparing only `HH:MM` would miss an 08:00–08:30 walk overlapping an 08:15 feeding. Comparing full date/time intervals handles that case and avoids treating the same clock time on different dates as a conflict.

Recurrence needed a similar refinement: the next occurrence is based on the task's due date, rather than the current date. Completing a task twice must not create two follow-up tasks. Automated tests check both decisions, including year boundaries and midnight overlaps. These checks provide stronger evidence than a plausible-looking demo alone.

## 4. Testing and Verification

### a. What was tested

The tests cover task creation and completion, adding tasks to pets, multi-pet aggregation, sorting, combined filters, daily and weekly recurrence, conflicts, invalid inputs, and task edits. Planning tests check priorities, available gaps, exact window fits, overdue tasks, and deferred work. Persistence tests verify that dates, IDs, preferences, and completion status survive a JSON round trip.

Streamlit tests exercise adding a pet, creating and editing a recurring task, completing it, and keeping data through reruns. They also cover filters, preferences, plan generation, and confirmation before replacing a household with sample data. The CLI demo and browser walkthrough provide additional end-to-end checks, including downloading and restoring a backup.

### b. Confidence

My confidence rating for the current scope is 4/5. All 41 tests pass locally, and GitHub checks pass on Python 3.11 and 3.12. That gives good coverage of a small household using local calendar times. The next areas to test would be larger households, very large imports, keyboard-only navigation, and behavior across more browsers.

## 5. Reflection

### a. What went well

The strongest part of the project is the separation between the domain model and the interface. The CLI, Streamlit app, and persistence layer all use the same classes, so scheduling rules do not have to be duplicated. Incremental commits also make the progression from UML to working application easy to follow.

### b. What could improve

In another iteration, I would add hard deadlines, support for multiple caregivers, and optional grouping of activities that can happen together. I would also explore a better optimization strategy when several tasks compete for a short care window. The current backup system is deliberately simple; a larger application would benefit from authenticated accounts and persistent storage.

### c. Key takeaway

The main takeaway is that clear rules and verification matter as much as generating code. A schedule can look reasonable while still mishandling a repeated click, a date boundary, or a saved backup. Defining class responsibilities first and testing those edge cases makes the system easier to explain, maintain, and extend.
