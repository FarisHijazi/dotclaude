---
argument-hint: [--dry] [substring | N]
description: Triage open items in the TODO file (inbox) and route each to inline / subagent / new tcc session; tick back into the file
---

# /todo - thin orchestrator over a TODO file

Inbox = `${TODO_FILE:-~/TODO.todo}` (todo.txt-ish: `- [ ] text`, tags like `@low`, `@done(YY-MM-DD)`).
The file is the only state. No DB, no queue, no gateway. tmux is the registry for spawned sessions.
Args: `$ARGUMENTS`. `--dry` = print the routing table and stop (change nothing). A substring or
line number restricts to matching items. Default scope: unchecked `- [ ]` items outside a
`## Garbage` section, skipping `@low` unless named explicitly, skipping lines that already carry
`@tcc(`, `@agent`, or `@you`.

## 1. Classify every item (do this yourself, cheaply - do NOT start working yet)

First match wins:

1. **YOU** - needs the human or a third party: physical action, a login/MFA, a decision, a message
   to a person ("ask X", "talk to X"), spending money. Do not spawn. Tag the line `@you`.
2. **INLINE** - doable in <= 3 tool calls with no real reading (one command, one-line edit, one
   lookup, writing a note). Do it now, in this session.
3. **AGENT** (subagent, `run_in_background`) - read-heavy or research: investigate, compare,
   "see if X works", audit, find options. Self-contained, no questions for the user, result is a
   report. Output goes to `docs/research/<YYYY-MM-DD>/<slug>.md`; only a <= 200-word summary
   comes back. Independent items go out in ONE message (parallel).
4. **TCC** (new tmux session) - anything that edits code/config in a repo, runs > ~15 min, lives
   in a different project directory, needs its own branch/worktree, or may need to ask the user
   something mid-way (a visible session in the `tw` hub beats a hidden subagent). Same repo as
   another running item: separate worktree under `<repo>/worktrees/<name>/`.

Tie-break when unsure: read-only -> AGENT, anything that writes -> TCC. Big ambiguous item
("rewrite X in rust") -> TCC whose first job is a plan, never a blind big-bang.

## 2. Show the table, then act

Print: `# | item (<= 60 chars) | route | why (<= 8 words) | dir`. With `--dry`, stop here.
Otherwise execute without asking, EXCEPT TCC items that are destructive or outward-facing
(sends, deploys, deletes, payments): list those as needing a yes.

## 3. Dispatch

- INLINE: do it, verify, then tick.
- AGENT: `Agent` tool, background, prompt = the item text + relevant paths + "write findings to
  docs/research/<date>/<slug>.md, reply < 200 words". Tag the line `@agent`.
- TCC: spawn detached, never switching the user's client:
  `env -u TMUX tcc-bg <dir> "<worker prompt>"` (prints the session name). Tag the line
  `@tcc(<session>)`. Worker prompt must contain: the item verbatim, the context paths, the
  definition of done (tested), and the closing duty: "when finished, in <TODO file> change this
  exact line's `[ ]` to `[x]`, append `@done(<YY-MM-DD>) - <one line result>`, then stop. If
  blocked on the human, replace `@tcc(...)` with `@you(<what you need>)`."
  Workers never edit any other line.

## 4. Write back (small, line-local edits only)

- Edit the single line (Edit tool, exact text match). Never rewrite or reorder the file.
- Tick `[x]` + `@done(YY-MM-DD) - <result>` ONLY after verification (INLINE) or when the
  subagent's report shows the thing works. Otherwise leave `[ ]` and keep the tag.
- Subagent finished -> next `/todo` run ticks it (or you do, on completion notice).

## 5. Finish

End with the table's final state: counts per route, session names to look at, and the
`@you` items (what exactly is needed). Keep it short.
