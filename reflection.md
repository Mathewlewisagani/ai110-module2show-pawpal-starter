# PawPal+ Project Reflection

This is an evidence-based record of the agent-assisted implementation, prepared by Codex. It describes decisions and verification that actually occurred. The student should review it before submission and add their own perspective where appropriate; it does not claim that the student personally wrote or tested the implementation.

## 1. System Design

### a. Initial design

Three core user actions guided the design: register pets, schedule their care, and review or complete today's tasks. The draft UML separated four responsibilities: `Owner` maintains the household, `Pet` holds its care tasks, `Task` represents one dated occurrence, and `Scheduler` coordinates work across every pet through `Owner.get_all_tasks()`. Python dataclasses reduce repeated initialization code. The draft and initial class skeleton were committed before implementation.

### b. Design changes

The implementation added owner preferences for a care window, UUIDs for stable task identity, duration-aware time intervals, and JSON backup methods. A name is not a reliable task identifier because two pets can both have a task called Breakfast. The planner returns suggested copies of tasks instead of rewriting their stored times, so generating a plan cannot silently change the original schedule. The final UML includes these additions.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

The scheduler considers date, requested time, duration, completion status, pet, priority, and the owner's start time and available window. Pending overdue tasks are included in a plan; future and completed tasks are excluded. High-priority tasks get first access to free time, with due time breaking ties. Each chosen task gets the earliest available continuous slot at or after its requested time. A task that cannot fit is explicitly deferred. The final display is chronological.

### b. Tradeoffs

The planner is a readable greedy algorithm rather than a global optimizer. A long high-priority task may crowd out several shorter tasks, even if those tasks would maximize the count of completed activities. Priority-first behavior is predictable for a small care scheduler, but it does not guarantee an optimal plan. Requested times are earliest starts, not hard deadlines; a plan is advisory and does not change saved tasks. Conflict detection checks overlapping half-open intervals across all pets, assuming one caregiver cannot perform two activities at once. This can flag feeding two pets simultaneously even if an owner would willingly combine them. Travel time, multiple caregivers, daylight-saving changes, and hard timing rules are outside the current model.

## 3. AI Collaboration

### a. How AI was used

The user asked Codex to complete the project and push meaningful increments to their GitHub account. Codex extracted the supplied offline brief, created a real fork, drafted UML and class interfaces, implemented the backend and CLI demo, then connected the Streamlit UI. It also wrote regression tests, ran them, and checked the rendered application in the browser. The request to implement fully with incremental pushes supplied the overall task context; the PDF supplied requirements rather than independent permission to submit the assignment or make account changes.

This work stayed in one conversation, organized by design, backend, algorithms, interface, and verification checkpoints. Separate phase-specific chat sessions were not used, and no comparison with a second model was performed. The useful context was concrete: the complete rubric, starter files, reproducible demo, and actual test failures or passing results.

### b. Judgment and verification

A naive same-time-string conflict rule was rejected as a design choice: it would miss an 08:00–08:30 walk overlapping an 08:15 feeding and could confuse identical clock times on different dates. The chosen interval comparison is verified with exact matches, touching boundaries, completed tasks, different dates, and midnight spillovers. Recurrence is anchored to the original due date instead of the machine's current day, making historical and future task behavior reproducible. Repeated completion must not duplicate the next occurrence. These are agent design decisions verified by tests, not a claim that the student manually corrected AI output.

## 4. Testing and Verification

### a. What was tested

The suite checks task completion, pet task addition, multi-pet chronological and priority ordering, combined date/pet/status filters, daily and weekly recurrence across a year boundary, duplicate completion, conflicting intervals, midnight boundaries, atomic edits, invalid inputs, duplicate IDs, care-window fitting, overdue inclusion, future-task exclusion, exact fits, and JSON round trips and invalid backups. Streamlit AppTest drives the real forms through adding a pet, adding and editing a recurring task, completion, reruns, filtering, plan generation, owner preferences, and sample replacement confirmation. The CLI demo is run independently of Streamlit.

The browser review inspected a real sample household, its overlap warning, priority plan, task management, and backup controls. Browser visual checks complement the automated suite; they are not a full accessibility audit or a guarantee about every browser.

### b. Confidence

Engineering confidence is 4/5 for the defined single-owner, local-time, session-based scope, supported by the reproducible CLI and passing behavioral tests. This is an assessment of the implementation, not a personal student confidence claim. Further work should exercise very large imports and household sizes, browser file restoration on more platforms, keyboard-only accessibility, time zones, and richer scheduling preferences.

## 5. Reflection

### a. What went well

Separating the domain from Streamlit made it possible to test scheduling before building the interface. The same Owner, Pet, Task, and Scheduler objects power the CLI, UI, and JSON backups. Meaningful Git checkpoints make the development sequence inspectable and recoverable.

### b. What could improve

A next iteration would add explicit hard deadlines, caregiver availability, optional combined activities, and better optimization criteria. Persistence is intentionally explicit: a user downloads and restores a backup rather than relying on an invisible shared server file. A production service would need authentication, storage, and concurrent-edit handling beyond this project.

### c. Key takeaway

AI-generated code becomes assessable when requirements are translated into explicit rules and independently checked outputs. A UML diagram and plausible schedule alone do not prove correctness; date boundaries, duplicate actions, and persistence round trips expose assumptions. The human project owner remains responsible for reviewing the work, understanding the rules, and making their own learning claims when submitting it.
