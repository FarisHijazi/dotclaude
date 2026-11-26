---
name: divide-conquer
description: Build or change a confidential project using coding subagents without any single subagent learning what the project is or what the others are doing. You (the orchestrator) keep the whole picture privately, cut the work into stand-alone "university assignment" style pieces with exact specs and tests, hand each piece to a fresh blind worker, re-run their tests, and wire the results together. Use this whenever the user says a project is confidential, secret, private, under NDA or "must not be seen by the model", asks to silo / compartmentalize / isolate agents, says divide and conquer, or wants strong models to do the coding without knowing the bigger picture, even if they do not name this skill.
---

# Divide and conquer a confidential project

You are the orchestrator. You are the only one who knows what this project is. Workers are stronger
programmers than you, so the plan is simple: **you describe small, exact, stand-alone problems; they
solve them completely; you do only bookkeeping and thin wiring.**

Why it works: a problem set from a university course never explains the company behind it. "Merge
overlapping intervals" could belong to a calendar, a genome tool or a missile. A worker that sees only
such a problem cannot work out the project, and a worker that never hears about the other problems
cannot put the picture together.

So there are three things you must keep true the whole time:

1. **No worker sees the purpose.** Not the project name, not the domain, not the customer, not why.
2. **No worker sees another worker's assignment**, or learns that other assignments exist.
3. **Workers do the hard part.** If you find yourself writing real logic, stop: that is an assignment.

A helper script does the bookkeeping so you do not have to remember it. Everywhere below, `DC` means:

```text
python3 <this skill's folder>/scripts/dc.py
```

## Step 1. Set up

```text
DC init <project folder>
```

This creates a private folder `<project>/.dc/` (your notes; hidden from git) and an assignments
folder **outside** the project. Workers only ever get paths in the assignments folder.

Now fill in two private files:

- `.dc/secret_terms.txt`: every word that would give the project away. Project name, codename,
  company, customers, competitors, people, product names, the words that name the domain and the
  goal, real URLs and hostnames, real table/file/class names that are revealing. Be generous: this
  list is what the automatic leak check uses, so a word missing here is a word that can leak.
- `.dc/PLAN.md`: what the project really is, and the list of pieces (Step 2).

## Step 2. Cut the project into pieces

Read the whole project (or the whole request, if nothing is built yet). Then write the Pieces table
in `.dc/PLAN.md`. A good piece:

- **Has a narrow doorway.** A few functions or one class, with inputs and outputs you can write down
  completely. Cut where little data crosses, not through the middle of a busy area.
- **Is a generic problem.** It can be titled like a textbook exercise: "rate limiter", "CSV
  normalizer", "priority scheduler", "fuzzy matcher", "retrying HTTP client". If the only honest
  title names the project's purpose, the piece is too big or too specific. Cut it smaller, or apply
  the next rule.
- **Has the secret taken out and passed in.** The secret is almost always *data*, not logic: the
  names, the URLs, the thresholds, the prompts, the rules table, the target list. Make those a
  parameter or a config value. The worker builds "a scorer that takes weights"; you supply the
  weights later. List these under "What stays with me" in PLAN.md.
- **Is one sitting of work.** Roughly one file to a small handful of files. Prefer more, smaller
  pieces over fewer, bigger ones: smaller pieces reveal less and fail less.
- **Does not need to know its neighbours.** If piece A calls piece B, A's assignment gets B's
  *interface* and a simple fake of B, never B's assignment or purpose.

Also watch the **combination**. Two harmless pieces can give the game away together, which is why
each goes to a different worker.

Working in an existing codebase: the same rules apply. A piece is then "rewrite/extend this module to
this spec". You may paste existing code into `starter/`, after renaming anything revealing in it.

Write every data shape that crosses between two pieces **once**, under "Shared interfaces" in
PLAN.md, and paste it unchanged into both assignments. Pieces that disagree about a shape are the
main way this method fails, and you are the only one who can prevent it.

What is left for you after cutting should be only: the config holding the secret values, and one
wiring file that creates the pieces and connects them. If the wiring is more than plain "create A,
create B, pass A to B", turn the complicated part into another assignment ("adapter between interface
X and interface Y").

## Step 3. Write each assignment

```text
DC new <project> A01 --dest <folder in the project for the code> --tests-dest <folder for its tests>
```

This creates the assignment folder with a template `ASSIGNMENT.md`. Fill in **every** `<<...>>`
placeholder. The worker has only this document, so the quality of the result is the quality of this
page. Before writing, read `references/writing-assignments.md` (a complete good example and the
common mistakes).

The non-negotiables:

- **Exact interface**: real signatures with types, in a code block.
- **Numbered rules** (R1, R2, ...): one behaviour each, each one checkable by a test.
- **Errors table**: every bad input and exactly what must happen.
- **At least five worked examples** with real values, including an empty case, a boundary case and
  an error case. Work each one out by hand and check it against your own rules. Examples are where
  your intent survives even if your rule wording is off.
- **Neutral names everywhere**: title, function names, field names, example values. Use made-up but
  ordinary values ("alice", "item-17", 42), never real ones.
- **Examples use different numbers from the real ones.** If the real limits are 40 to 75 over 180
  days, write the examples with 10 to 20 over 7 days. The real numbers are part of the secret, and
  the leak check cannot catch a number.
- **Collaborators as fakes**: for anything the piece calls, put the interface in the assignment and a
  small fake in `starter/`.
- **Acceptance tests** in `tests/acceptance/` if you can write them (turning your worked examples
  into tests is enough). The worker writes the rest of the tests; that is part of their job.
- If the piece is not Python, edit `run_tests.sh` in the assignment folder to the right test command.

## Step 4. Check for leaks

```text
DC check <project>
```

It fails an assignment that contains a secret term, an unfilled placeholder, a missing section, or
too few examples. Fix and re-run until every assignment says OK.

The script only catches listed words. So also read each assignment once as a stranger and ask:
**"If this were all I had, could I guess what the project is?"** If yes, rename, generalize, or cut
the piece smaller, and add the telltale words to `secret_terms.txt`.

## Step 5. Dispatch

For each assignment:

```text
DC prompt <project> A01
```

It prints the exact prompt for the worker. Start **one new subagent per assignment**, using your
strongest available coding model, and give it that printed text **and nothing else**.

- Do not add a greeting, background, a hint, or "this is part of ...". The prompt is the place leaks
  happen most easily, which is why it is generated for you.
- Do not reuse a worker for a second assignment, and do not continue an old worker with a new piece.
  A fresh worker knows nothing; a reused one has seen two pieces.
- Independent pieces can be dispatched at the same time.
- If the project folder has a `CLAUDE.md`/`AGENTS.md` or similar that describes the project, subagents
  started from that folder may be shown it automatically. In that case start workers from the
  assignment folder instead (for example `cd <assignment folder> && claude -p "<the prompt>"`).

## Step 6. Receive and verify

Do not trust a worker's "done". Run:

```text
DC verify <project> A01
```

It checks that the worker reported `Status: DONE`, did not edit the spec or the acceptance tests, and
it re-runs the tests itself. Then read the worker's `SUBMISSION.md`: "How to call it" is your wiring
recipe, and "Assumptions" / "Spec problems" tell you where your spec had holes.

When it does not pass, write `FEEDBACK.md` in the assignment folder and dispatch again with
`DC prompt` (a **fresh** worker is fine; the folder carries the state):

- Status `QUESTIONS`: answer each question in FEEDBACK.md in spec language. If the answer changes a
  shared interface, update PLAN.md and every assignment that uses it.
- Tests failed: paste the failing output into FEEDBACK.md.
- An assumption the worker made is wrong for the project: state the correct rule in FEEDBACK.md with
  an example. Do not explain *why* it is the correct rule if the why is the secret.

FEEDBACK.md is seen by a worker, so it follows the same no-secrets rules. `DC check` scans it too.

## Step 7. Integrate and test the whole thing

```text
DC integrate <project> A01
```

copies the verified code (and tests) into the project. When all pieces are in:

1. Write the config with the real secret values and the wiring file, following each "How to call it".
   Workers import their own files by plain name (`from offset import adjust`), so the wiring and the
   test command must put each `--dest` folder on the import path (in Python: `PYTHONPATH=<dest>`).
2. Run the whole-project test from PLAN.md.

When the whole-project test fails, do not debug deep logic yourself. Find **which doorway** the wrong
value crossed (print what goes into and comes out of each piece), then send it back to that piece as
FEEDBACK.md: "given this input the output was X, expected Y", with values made neutral. If two pieces
each match their spec but do not fit each other, the specs disagree: fix the shared interface in
PLAN.md and send both a revision.

`DC status <project>` shows where every assignment stands at any time.

## What to tell the user at the end

- which pieces were built and that the whole-project test passes (show the output);
- anything you wrote yourself (it should only be config and wiring);
- any assumption a worker made that the user should confirm.
