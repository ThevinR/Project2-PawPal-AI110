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

My scheduler considers four things. The **owner's available minutes** is the only hard constraint — nothing can be planned once the budget runs out. **Priority** decides what gets that time first, since a HIGH task is one the owner shouldn't miss. **Preferred time** is a soft preference used as a tiebreaker inside a priority band, and separately as the basis for conflict detection. **Duration** is the final tiebreaker, so two equally urgent tasks at the same hour put the shorter one first.

I decided the order by asking what actually hurts the pet if it goes wrong. Missing a medication matters more than doing a walk at a slightly odd hour, so priority had to outrank preferred time. That is why `sort_tasks` keys on `(-priority, has_no_time, preferred_time, duration)` in exactly that order, and why `generate_plan` only ever checks minutes rather than trying to lay tasks out on a clock. Treating available time as hard and preferred time as soft is the single decision that shapes the rest of the system.

**b. Tradeoffs**

My scheduler only warns about time conflicts; it does not resolve them. `detect_conflicts` finds tasks whose preferred-time windows overlap (start time plus duration, so a 30-minute task at 07:30 clashes with one at 07:45, not just an exact match). `conflict_warnings` turns those pairs into messages, and `generate_plan` keeps building the plan anyway. The plan is chosen by priority and available minutes, not by clock time, so two overlapping tasks can both end up in it with a warning attached.

I also kept the simple version of the conflict check. The AI suggested sorting tasks by start time and breaking out of the inner loop early, which is faster, but it makes the overlap condition harder to follow. My version compares every pair, which is O(n²) but easy to read. A pet owner has tens of tasks a day, so the speed difference doesn't matter, and I would rather be able to read and debug the code.

This is reasonable here because a preferred time is a preference, not a hard rule. If the scheduler silently moved or dropped a task, the owner could miss a medication or feeding without realizing it. A warning lets the owner decide what to move. The cost is that the plan can contain a clash the owner has to fix by hand.

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

**c. AI strategy**

*Which AI assistant features were most effective?*

Three were worth far more than plain code generation.

**Reading my actual files instead of describing them.** The assistant could open `pawpal_system.py` and `test_pawpal.py` directly, so when I asked for a test plan it came back with gaps in *my* code — the midnight wraparound in `_minutes()`, the zero-duration case in `detect_conflicts` — not generic advice about scheduler testing. Pasting snippets into a chat box never produced that quality of answer, because the assistant couldn't see what already existed.

**Running commands and reading the results.** It executed `python -m pytest` and `python main.py`, so the pytest output and CLI output in my README are real runs rather than invented examples. It also launched the Streamlit app and checked the server actually responded before telling me the UI changes worked. That closes the loop that normally breaks with AI code: the difference between "this should work" and "I ran it."

**Asking it to find problems rather than produce code.** The single most useful prompt in the whole project was "review my skeleton for missing relationships or potential bottlenecks." That one question produced the unique task ids and the `pet_name` field, which are now load-bearing for the whole multi-pet design. Review prompts consistently outperformed build prompts.

*One suggestion I rejected or modified.*

The clearest rejection was the five-class design described above, but a smaller one shows the point better. When I asked for tests, the assistant proposed tests that would have **fixed** the two bugs it found — adding an `is_completed` guard to `mark_complete()` and a midnight modulo to `_minutes()`. I modified that. Instead of silently changing the scheduling rules late in the build, I had it write tests that *document* the current behaviour, with docstrings saying exactly what would change if I decided to fix it:

```python
def test_completing_the_same_task_twice_recurs_twice():
    """Documents current behaviour... If PawPal+ should treat
    re-completion as a no-op, this test is the one to flip."""
```

I kept my design decision and made the limitation visible instead of letting the assistant quietly redefine what "complete" means. Both limitations are now named in the README rather than hidden. A test that records a known flaw is more honest than a fix I hadn't thought through.

I also modified its first pass at the Streamlit UI. It wired the display to the Scheduler methods as asked, but to make conflict warnings fire it had to add preferred-time and frequency inputs to the form — a scope expansion beyond "update display logic." It flagged that it had done so rather than burying it, which let me confirm the change was one I wanted.

*How separate chat sessions per phase helped.*

I ran each phase in its own session: design and UML, implementation, sorting and filtering, testing, then documentation. The benefit was that each session started with one job and no accumulated baggage. In the testing session the assistant wasn't still arguing for the five-class design from the design session; it just read the finished code and found gaps in it.

It also made the git history clean, because each session mapped to roughly one commit (`refactor: add enums, task ids...`, `feat: implement sorting, filtering, and conflict detection`). And it forced a useful discipline: starting fresh meant I had to re-state the goal in my own words each time, which is how I noticed the UML had drifted from the code — I couldn't describe the system without checking which version was true.

The cost is real: context doesn't carry over, so the documentation session had to re-read every file. That re-reading is what caught the unclosed code fence in the README that earlier sessions had written and never looked at again.

*What I learned about being lead architect.*

The assistant was faster than me at everything except deciding what the system should be. That turned out to be the whole job.

Every significant design decision in PawPal+ was one I made and the AI executed: four classes instead of six, warn-don't-resolve for conflicts, available minutes as the only hard constraint, O(n²) readable conflict detection over a faster version I'd struggle to debug. Each time, the AI had a defensible alternative. None were wrong exactly — they were answers to a slightly different question than the one I was asking, usually a more general one. A general-purpose scheduler probably *should* resolve conflicts. A pet-care assistant where a missed medication is the failure mode should not.

The practical lesson is that the quality of what I got back tracked the quality of the constraint I gave. "Write a scheduler" produced something elaborate and generic. "Give the Owner one method that returns every pet's tasks" produced exactly the right four lines. Being the architect meant doing the narrowing work myself before asking — knowing which of the two sorts a given screen needs, what a conflict warning is allowed to do, when a limitation is acceptable. The AI could implement any answer I picked, and would have implemented a bad one just as fluently. Nothing in the tooling told me which answer was right for a busy pet owner, and I think that's the part that doesn't get automated.

---

## 4. Testing and Verification

**a. What you tested**

I ended with 34 tests in `tests/test_pawpal.py`, grouped into four areas: sorting, recurrence, conflict detection, and plan generation. Within each I wrote both happy paths and edge cases, because the happy paths tell me the feature works and the edge cases tell me *where it stops working*.

The tests I consider most important aren't the obvious ones:

- **An oversized task is skipped but a later shorter task still fits.** This is the core of the greedy planner. If the loop broke on the first task that didn't fit, one 90-minute grooming session would wipe out the owner's entire day. The test is the only thing guarding that behaviour.
- **Identical tasks keep insertion order in both sorts.** When every sort key ties, the order comes from Python's `sorted()` being stable. Without a test, that is accidental behaviour that a refactor could silently break.
- **Back-to-back tasks don't conflict.** `detect_conflicts` uses half-open windows, so a 30-minute task at 08:00 and one at 08:30 are fine. Getting this wrong would make the app cry wolf on a perfectly sensible schedule, and users ignore warnings that fire constantly.
- **A pet with no tasks, an owner with no pets, zero available minutes.** Empty states are where a naive implementation throws instead of returning an empty list, and they're the first thing a real user hits.
- **Completing a task twice, and a task running past midnight.** These two document bugs rather than correct behaviour, which I think is the right call for limitations I chose not to fix inside this iteration.

**b. Confidence**

Four stars out of five, which is also what I put in the README.

I'm confident about the core scheduling logic. Every behaviour I documented has a passing test behind it, including the tie-breaking and empty-state cases where bugs usually hide, and the whole suite runs in under a tenth of a second so I actually run it. The CLI demo's output matches what the tests predict, which is independent confirmation that the pieces work together and not just in isolation.

The missing star is for two things I know are wrong and chose to document rather than fix: time windows don't wrap around midnight, so a 23:50 task never clashes with an 00:05 one; and completing an already-completed recurring task spawns a duplicate occurrence. Neither is hypothetical — both have tests proving they happen.

With more time, in order: the **double-completion guard**, since it corrupts data rather than just reporting something odd. Then **midnight wraparound**, which needs `_minutes()` to handle tasks crossing day boundaries. Then **negative or absurd durations**, which nothing currently rejects — the Streamlit form enforces a minimum of 1 but `Task` itself doesn't, so the UI is doing validation that belongs in the model. I'd also test **MONTHLY recurrence** if I added it, because month arithmetic breaks in ways `timedelta` can't express (what is one month after January 31?). And finally the **Streamlit layer itself**, which has no tests at all right now; I verified it only by running it and checking it responded.

---

## 5. Reflection

**a. What went well**

The separation between the data classes and the Scheduler is the part I'd defend hardest. `Task`, `Pet` and `Owner` hold data and almost nothing else; every scheduling rule lives in one class. The payoff showed up when I built the Streamlit UI: the filter dropdowns, the sort toggle and the conflict banner all call `Scheduler` methods directly, so the UI has essentially no logic of its own. That means what the app displays and what the tests verify are literally the same code paths. If I'd written the filtering inline in `app.py` — which was the obvious shortcut — the UI could have drifted from the tested behaviour without anything failing.

I'm also satisfied with `explain_plan()`. It was the last thing I added and the one that made the app feel like an assistant rather than a list, because it states what was planned, what was skipped and *why there wasn't room*. A schedule that silently omits grooming is confusing; one that says "not enough time left" is useful.

**b. What you would improve**

Two things, one small and one structural.

The small one: `Scheduler` became stateful when I added `self.plan` and `self.skipped`, which means `explain_plan()` depends on `generate_plan()` having been called first. That's an implicit ordering a caller can get wrong, and it's why I had to add a test that regenerating a plan resets the previous results. A cleaner design returns a `Plan` object holding the planned tasks, the skipped ones and the warnings together — which is, I'll note, close to the `DailyPlan` class the AI proposed on day one and I rejected. I still think four classes was right for the version I was building; I just now understand what the fifth would have bought me.

The structural one: `generate_plan()` fits tasks by total minutes and ignores the clock entirely, which is why a plan can contain two tasks at 09:00. Given more time I'd make the planner time-aware — walk the day chronologically, place tasks in actual slots, and either report an unresolvable clash or suggest the nearest free window. That's a real algorithm change, not a tweak, and I'd want the conflict tests in place first, which they now are.

**c. Key takeaway**

The decision I'm proudest of is one where the scheduler does *less*: it warns about conflicts instead of resolving them. It would have been easy, and would have looked more impressive, to auto-shuffle overlapping tasks. But a preferred time is a preference to the program and a vet appointment to the owner, and software that silently moves a medication is worse than software that points at the problem. Working out which parts of a system should have authority and which should only advise taught me more than any of the code did.

On the AI side: the assistant never once asked me *why* a feature should work a particular way. It would implement conflict resolution or conflict warnings with equal confidence and equal fluency. Knowing which one this app needed required understanding the user — a busy pet owner who'll lose trust the first time the app moves something important without asking. That judgment was the part I had to supply, and it's the part I'd supply again on a bigger project.
