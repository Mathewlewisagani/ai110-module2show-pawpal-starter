# PawPal+ Project Reflection

## 1. System Design

### a. Initial design

The three main actions are adding a pet, scheduling a task, and checking today's tasks.

The design uses four classes:
- `Owner` stores the owner's name, pets, and available care time.
- `Pet` stores a pet's name, species, and tasks.
- `Task` stores the activity, date, time, duration, priority, and completion status.
- `Scheduler` gets tasks from all the owner's pets and organizes them.

Dataclasses keep the classes simple. The draft UML shows how they connect.

### b. Design changes

The final version adds task IDs, JSON storage, and a care window. IDs help tell apart tasks with the same name. The scheduler also checks task durations, not just start times. Generating a plan leaves the original task times unchanged.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

The scheduler considers time, duration, priority, and the owner's care window. High-priority tasks come first, then due time. Completed and future tasks are left out of the plan. Overdue tasks are included. Tasks that do not fit are shown as deferred.

### b. Tradeoffs

The planner uses a greedy algorithm. It picks a slot for each task in priority order instead of trying every possible schedule. This is easier to follow, but a long high-priority task might take space that several shorter tasks could use.

It assumes one caregiver. Requested times are earliest start times, not strict deadlines. It does not handle travel time or time zones.

## 3. AI Collaboration

### a. How AI was used

AI helped turn the UML into Python classes, write scheduling methods, connect Streamlit, and suggest tests. Giving it the class names, recurrence rules, and multi-pet requirement made the requests more specific.

The work was split into design, backend, algorithms, UI, and testing stages. It stayed in one chat, with separate commits for each stage.

### b. Judgment and verification

I kept the recurrence approach that checks the frequency and creates the next task before marking the old one complete. I did not use the other model's shorter `.get()` version because the explicit checks were easier to read. Both passed the same tests.

A start-time-only conflict check was too limited. Comparing full time intervals also catches a walk from 08:00 to 08:30 overlapping a feeding at 08:15. Tests check this, daily and weekly recurrence, date boundaries, and repeated completion.

## 4. Testing and Verification

### a. What was tested

Tests cover adding tasks, completion, sorting, filtering, conflicts, recurrence, priority planning, edits, and JSON storage. UI tests check forms and reruns. A fresh app session also reloads the saved pets and tasks.

The CLI demo shows two pets and several tasks. The browser check includes downloading and restoring a backup.

### b. Confidence

My confidence is 4/5. All 57 tests pass, and GitHub checks pass on Python 3.11 and 3.12. More testing could cover larger households, more browsers, and keyboard-only use.

## 5. Reflection

### a. What went well

The backend works separately from Streamlit. The CLI and UI use the same classes, so the scheduling rules are in one place.

### b. What could improve

I would add strict deadlines, multiple caregivers, and better ways to fit tasks into a short window. JSON works for this local app, but a bigger app would need accounts and a database.

### c. Key takeaway

A schedule can look right and still have bugs. Clear class responsibilities and tests for things like duplicate completion and date changes make the app easier to check and improve.
