---
argument-hint: [optional output path or suffix]
description: Gather all user asks/tasks/instructions from the current conversation into a standalone TASK_*.md file that someone with no context could execute.
---

## Task

Review the **entire current conversation** and extract every ask, task, or instruction the user gave. Then write a self-contained handoff file that someone with **zero prior context** could pick up and execute successfully.

### Step 1 — Collect

Scan the whole conversation (from the first user message to the latest) and collect:

- Every explicit request, task, or instruction from the user (including ones already completed, revised, or abandoned — note the status).
- Any clarifications, corrections, or constraints the user added along the way.
- Any decisions made, approaches agreed on, or approaches rejected.
- Relevant context the new executor would need: file paths, repo/branch, environment, tools/commands used, credentials/access requirements (by name, not value), external systems referenced.
- Any outputs already produced (files created/edited, commands run, findings) so the new person isn't told to redo finished work — unless the user wants it redone.
- **Everything that was already attempted**, including failed attempts, partial progress, dead ends, and why they failed. The next person needs to know what not to repeat and what's still in a half-done state.
- **What worked vs what didn't work**: approaches that produced the desired result, approaches that were tried and abandoned, error messages encountered, workarounds applied.

If the user passed `$ARGUMENTS`, treat it as either a desired output path or a filename suffix (see Step 3).

### Step 2 — Deduplicate and order

- Merge duplicate/overlapping asks.
- Drop side-chatter that isn't an instruction.
- Order tasks in the sequence they should be executed (dependencies first), not in the order they appeared in chat.
- Separate **completed** vs **remaining** work clearly.

### Step 3 — Write the file

Filename: `TASK_<short-kebab-description>.md` in the current working directory.
- If `$ARGUMENTS` looks like a path ending in `.md`, use it verbatim.
- If `$ARGUMENTS` is a short label, use `TASK_<label>.md`.
- Otherwise generate a short kebab-case description from the dominant theme of the tasks.

Use this structure:

```md
# Task: <one-line title>

## Goal
<2–4 sentences: what the user ultimately wants accomplished and why. Written so a stranger understands the point.>

## Context
- Repo / working directory: <path>
- Branch: <branch if relevant>
- Relevant files / systems: <list>
- Access / tools needed: <list by name>
- Anything already done that should NOT be redone: <list or "none">

## Constraints and preferences
<Bullet list of user-stated rules: style, libraries to use/avoid, what NOT to do, deadlines, review requirements, etc.>

## Tasks
1. <Task one — concrete, actionable, with acceptance criteria>
2. <Task two ...>
   - Sub-step if needed
3. ...

## Already completed (for reference, do not redo)
- <item> — <short note on outcome / where to find it>

## Attempted / tried / partial progress
What was already tried, whether it worked, and what state things are in now. The point is so the next person does not repeat dead ends or miss that something is half-done.
- **Worked:** <approach that succeeded and is now in place — where to see the result>
- **Didn't work:** <approach tried, the exact error / reason it failed, and whether it was abandoned or is pending retry>
- **In progress / partial:** <work that was started but not finished — current state, where the files are, what's left>
- **Ruled out:** <options considered and rejected, with the reason, so no one reopens the debate without new info>

## Open questions / decisions needed
<Anything the user left ambiguous that the executor should confirm before starting. If none, write "None.">

## Definition of done
<Checklist the executor can self-verify against before handing back.>
```

Rules for the file:
- **No references to "the conversation", "earlier you said", "as we discussed", or to Claude.** The reader has none of that.
- Inline any snippets, commands, or paths the executor needs — don't say "see above."
- Prefer concrete over abstract: real file paths, real command strings, real acceptance criteria.
- If the user gave verbatim wording that matters (e.g. exact copy, exact naming), quote it.
- Keep it tight. No filler, no restating the template headers if a section is genuinely empty — write "None." instead.

### Step 4 — Report back

After writing the file, reply with:
- The path to the file.
- A 1–2 sentence summary of what's in it (task count, main theme).
- Any **open questions** you flagged in the file that the user could answer right now to make the handoff cleaner.
