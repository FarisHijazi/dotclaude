# Rewrote the chat output format section

2026-09-02

Rewritten from an interview (`/grill-me`), not from guesswork. This records *why* each
rule is what it is; `CLAUDE.md` carries the rules themselves and deliberately does not
repeat this reasoning.

## The problem

The section had grown by accretion and contradicted itself in five places:

- `"Have no new line after the double heading sections"` was unparseable — I had been
  guessing at the spacing for an unknown number of sessions.
- `↩️` had no `##` while every other section did, so it was unclear whether it was a
  section at all.
- **Findings vs What was done** overlapped on anything discovered *and* fixed.
- **Not done vs Action needed** both wanted the same item, while a "no duplication" rule
  forbade exactly that.
- **Info needed** was defined only by what it was not.
- The rule that all four user-facing sections go into `AskUserQuestion` was being ignored
  outright — decisions went through the tool, actions and suggestions did not.

## The decisions

**The last four sections are exception reporting.** They are not a checklist to fill. An
item earns a place only when Claude is genuinely blocked, needs something only the user
has, or is naming out-of-scope work.

**`👤 Action needed` means human-only.** The sharpest rule of the set. If Claude can do a
thing, Claude does it — or it goes on Claude's own TODO. Auditing the session that
prompted this, most Action items failed the test: "drop the stash" and "delete the temp
dir" were both things Claude could have done, and "keep the backup" was a Finding in
disguise. Anything risky enough to need approval is a `🔀 Decision` where the user chooses
and *Claude* still executes — never a command handed over.

**`⭕ Not done` became `⭕ My TODO`.** It is Claude's backlog, which is why a non-empty
list is a reason to keep working rather than to stop and report. Turns end when the job
is done or Claude is stuck — never for a half-way progress update. A question asked
mid-flight gets answered on the `↩️` line while work continues.

**Sections are mutually exclusive.** Found *and* fixed is a Done line only; `🔍 Findings`
now holds strictly what was discovered and not acted on. This is what finally separates
Findings from Done and Not-done from Action.

**Section order never changes; item order does.** An earlier answer of "urgency floats to
the top" was corrected mid-interview: fixed sections keep the reader's eye trained, while
items inside a section sort by importance.

**Every item is prefixed with its section's emoji**, so an item still identifies itself if
the headings are dropped later — which is the stated intent.

**No item cap.** A number was considered and rejected: with the bars above doing the
limiting, a hard ceiling would only push Claude to merge or drop real items.

## Mechanics settled

`AskUserQuestion` fires whenever any of the four sections has an item, *after* the full
message including the trailing status token, in as many sequential calls as the item count
needs. No second formatted report once the user answers — Claude just continues. Spacing:
no blank line between a heading and its first item, one blank line before the next
heading.

Scope is normal turns only: not plan mode, not subagent reports.

Previous version backed up to the session scratchpad before replacement.
