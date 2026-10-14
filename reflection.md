# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML has four classes, with data kept separate from scheduling logic.

Task holds the details of one care activity: title, duration, priority, preferred time, frequency, and completion status.
Pet stores the pet's details and manages the list of tasks assigned to that pet.
Owner manages multiple pets and gives access to all of their tasks through methods like get_all_tasks().
Scheduler is the "brain" of the app. It retrieves tasks across all pets from the Owner object, then organizes, sorts, and filters them and detects conflicts to build the daily plan.
An Owner has Pets, a Pet has Tasks, and the Scheduler uses the Owner to reach every task. I used Python dataclasses for Task, Pet, and Owner to keep them simple, and made Scheduler a regular class because it carries the logic. Keeping the two separate means the scheduling rules can change without touching the data model, and the scheduler can be tested on its own.


**b. Design changes**

Yes, my design changed after I reviewed my first skeleton for missing relationships and weak spots. The biggest change was to Task. Tasks had no unique id, so removing one of two identical "Walk" tasks could delete the wrong one, and they didn't record which pet they belonged to, so a plan covering several pets couldn't say whose task was whose. I added an id and a pet name, and made remove_task use the id.

I also replaced the plain strings for priority and frequency with Enums, and used datetime.time for preferred times, because strings are easy to mistype and can't be sorted or compared reliably. I considered extra classes for a scheduled slot and a skipped task, but dropped them to keep the design at four classes. The Scheduler returns an ordered list of tasks and explains its choices instead.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI for design brainstorming, code generation, review, and testing. First I asked it to read the README and name the core user actions. Then I had it propose objects with attributes and methods, draw a Mermaid UML diagram, and turn that into Python dataclass stubs. After that I asked it to review the skeleton for missing relationships and bottlenecks, to implement the four classes, to write `main.py` as a demo, and to draft two tests. The most helpful prompts were specific and gave a clear target, such as "review my skeleton for missing relationships or potential bottlenecks" and "give the Owner one method that returns every pet's tasks."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I did not accept the AI's design as-is. It first proposed five or six classes, including ScheduledItem, DailyPlan, and SkippedTask. I reviewed that against my own four-class design (Task, Pet, Owner, Scheduler) and decided the extra classes added complexity without enough benefit, so I had the design cut back. I accepted its other suggestions: unique task ids, a pet name on each task, Enums for priority and frequency, and `datetime.time` for times. I rejected others as too much for this project, including a `last_completed` date for recurring tasks and an owner day-start time. I also made sure the Scheduler reads tasks through `Owner.get_all_tasks()` rather than from a single pet, so multiple pets are handled.

I verified the result in several ways. I compared the UML diagram against the code and found the diagram still showed the old five-class design, so I had it updated. I ran `main.py` with two pets and five tasks and checked the output by hand: the highest-priority tasks were planned, the low-priority grooming task was skipped for lack of time, and the explanation matched. That run also caught a bug where a broken newline in `explain_plan` stopped the file from loading, which was fixed before the tests ran. Finally, I ran two pytest tests in the project's virtual environment, one for `mark_complete()` and one for adding a task to a pet, and both passed.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
