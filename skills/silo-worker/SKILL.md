---
name: silo-worker
description: How to complete a single self-contained programming assignment handed to you as a folder containing ASSIGNMENT.md (a spec with an exact interface, numbered rules, worked examples and acceptance tests). Use whenever you are told "you have one self-contained programming assignment", pointed at a folder with ASSIGNMENT.md or HOW_TO_WORK.md, or asked to revise a submission from a FEEDBACK.md. Test-first, spec-exact, finished to a drop-in standard, reported in SUBMISSION.md.
---

# Completing a self-contained assignment

You have been handed one assignment folder. Treat it like a take-home problem set: everything you
need is in the folder, and nothing outside it is part of the task.

Two facts shape everything below:

1. **The spec is the whole truth.** You are deliberately not told what the code is for or what sits
   around it. Do not look for that context (no reading, listing or searching outside the folder),
   do not ask for it, and do not guess at it in your code, comments or report. Design decisions come
   from the written rules, never from a theory about the purpose.
2. **Whoever receives your work cannot repair it.** It will be dropped into place by someone with far
   less ability than you and no time to read your code. A submission that is 95% right costs them
   more than it saves. Finish it completely, and say plainly what you did not finish.

## The folder

```text
ASSIGNMENT.md        the spec (do not edit)
run_tests.sh         the test command (do not edit)
tests/acceptance/    tests supplied with the assignment, may be empty (do not edit)
starter/             supplied fakes and stubs for anything you call but do not own (do not edit)
src/                 your implementation goes here
tests/               your own tests go here
FEEDBACK.md          present only on a revision round
SUBMISSION.md        you write this last
```

Editing a do-not-edit file gets the whole submission rejected automatically. If one of them is wrong,
say so in SUBMISSION.md and work to the spec as written.

## Steps

### 1. Read and interrogate the spec

Read ASSIGNMENT.md fully, then `starter/` and `tests/acceptance/`. Before writing code, hunt for holes:
for each rule, ask what happens at empty input, at the boundaries, with duplicates, with ties, with
bad types, and when two rules apply at once. Check every worked example against the rules by hand.

Sort what you find:

- **A hole with one sensible reading** (the spec is silent, but an example or a neighbouring rule
  settles it): take that reading, note it under Assumptions, cover it with a test.
- **A hole where two sensible readings give different results through the public interface**, or a
  worked example that contradicts a rule: this is blocking. Do not guess. Write SUBMISSION.md with
  `Status: QUESTIONS`, list each question with the two readings and which you recommend, and stop.
  A wrong guess here is invisible until the whole thing is assembled, which is the most expensive
  place to find it.

On a revision round, read FEEDBACK.md first. Every failing case in it becomes a test before you
change any code.

### 2. Write the tests first

Before any implementation, write tests in `tests/` that pin the spec down:

- one test per numbered rule, named after it (`test_r3_...`), so a failure points at a rule;
- every worked example, verbatim;
- every row of the Errors table;
- the edges you found in step 1, including your assumptions;
- one start-to-finish test that drives the public interface the way a caller would, using the fakes
  in `starter/` for collaborators, across a realistic sequence of calls;
- if Limits gives a size or time, a test at that size.

Run `./run_tests.sh` and see them fail for the right reason (missing implementation, not a broken test).

### 3. Implement

- Match the Public interface exactly: names, argument order, types, file location. If you think the
  interface is poorly designed, implement it as written and say so in the report.
- Only the dependencies listed under Environment. No network, no files outside the folder, no global
  mutable state, no hidden randomness or clock reads unless the spec passes them in.
- Nothing from "Out of scope". No extras: extras are untested surface someone else has to own.
- Collaborators are reached only through the interface given in the spec, passed in rather than
  imported, so the real ones can be swapped in later without touching your code.

### 4. Prove it

Run `./run_tests.sh` from a clean state until it exits 0. Then reread ASSIGNMENT.md top to bottom
against your code one more time, rule by rule, looking for anything implemented from memory rather
than from the text.

### 5. Write SUBMISSION.md

Use exactly this template. The first line is read by a script.

```markdown
Status: DONE | QUESTIONS | BLOCKED

## Test results
Command: ./run_tests.sh
<the last lines of real output, pasted, including the pass/fail counts>

## Files
- src/...: one line on what it holds

## How to call it
<a complete copy-pasteable snippet: imports, constructing any collaborators, one call, the result>

## Assumptions
- <each hole you filled, the reading you chose, the test that covers it> (or "None.")

## Spec problems
- <contradictions, typos, rules that could not be tested, interface concerns> (or "None.")

## Not done
- <anything in the spec you did not deliver, and why> (or "None.")

## Questions
- <only when Status is QUESTIONS: the question, reading A, reading B, your recommendation>
```

`BLOCKED` means you cannot proceed for a reason that is not a spec question (a missing fake, a
dependency that is not installed). Say exactly what is missing.

Report only what you ran. If a test fails, the status is not DONE.

### 6. Reply

Your final message is the Status line and nothing else. The report is the file.
