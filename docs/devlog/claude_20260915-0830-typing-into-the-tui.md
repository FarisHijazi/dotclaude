# Typing into the Claude TUI: the /color abort, and a /theme setter

Two settings a running session will not re-read — the session colour and the
theme — so the only lever either has is a slash command typed into its own pane.
This is about making that reliable. Sibling docs:
`plugins-mcp-and-connectors.md` (what a plugin is on disk).

## The /color bug: aborting one keystroke before Enter

Reported as "failing to press enter or pressing enter too early". The log said
otherwise and said it precisely:

```text
ABORT before Enter — box holds '', expected '/color blue'
```

4 of 9 applies on the laptop, 1 of 5 on one VM.

`cc-color-apply.sh` already knew that a recognised slash command is drawn
coloured and that the default `cc-prompt-state` reading drops coloured runs, so
it used `--raw`. Necessary, not sufficient. Typing `/color` + a space **opens the
slash-command menu**, which moves the input row; `cc-prompt-state` then finds no
box at all and exits **2 with empty stdout**. The read-back captured stdout and
dropped the exit code, so "a menu is open" was indistinguishable from "our text
vanished" — and it aborted, leaving `/color blue` sitting unsent for whatever
typed there next to submit along with its own message. That is the other log
line: `box holds '/color bluefor aerospace with the external monitor...`.

The Enter-retry loop compared the same way, so it broke out on its first pass:
the retry that existed specifically for a swallowed Enter never ran.

Fix (cc-notify 1.8.5): when the box reads empty *or* unreadable, verify against
the **pane** (`still_typed`, the trick `auto-compact-continue.sh` already used
for `/compact`) before concluding anything. Only a box holding genuinely
*different* text still aborts — that one really is the user typing. `read_raw`
also folds U+00A0 and trims, so the comparison stops depending on whether
`[[:space:]]` matches NBSP (it does on macOS, not under glibc).

### Proving it, after failing to

Replaying the race with `CC_COLOR_ENTER_DELAY=0` did not reproduce it — old and
new both passed three runs. A race you cannot lose on demand is not evidence.
So the condition was simulated instead: a stub `cc-prompt-state` that exits 0
for the is-it-empty check and 2 for the `--raw` read-back, which is exactly what
an open menu does, pointed at a real session that really had the text typed:

```text
OLD 1.8.4 : exit=1   ABORT before Enter — box holds '', expected '/color red'
NEW 1.8.5 : exit=0   box read '' (rc=2) but '/color red' is on the row — proceeding
                     applied '/color red'
```

The old line is character-for-character the one from the real log.

## scripts/cc-theme.sh

`theme` is a plain `settings.json` key with seven values, but a **running**
session ignores a change to it — flipping it mid-session left the rendered
palette byte-identical. So the popup it is.

The popup opens with the cursor on the *current* theme, which is what makes
"send N Down presses" wrong from every other starting point, and the list grows
once a custom theme is saved. But the menu is numbered and **a digit selects
directly**. So: open the menu, read it off the pane, match the label exactly,
press that digit. Starting position stops mattering.

Exact-match on the label matters — `Dark mode` must not select
`Dark mode (ANSI colors only)`. `--list` prints the menu with the active entry
marked, which is also the cheapest way to see what a session is currently on.

## Rules for anything that types into a pane

1. Only into an **empty** box (`cc-prompt-state`), and hold the cc-notify
   type-lock so `/color`, `/compact` and this cannot interleave.
2. Never trust one reading. A coloured slash command reads empty; an open menu
   reads *no box*. Confirm against `tmux capture-pane`.
3. The UNSENT input row is `❯` + U+00A0 + text; a submitted echo uses an
   ordinary space. That NBSP is the whole difference between "waiting" and
   "gone" — and it is also the character that trims differently per libc.
4. On mismatch abort **without** backspacing. Leaving text unsent is untidy;
   eating characters someone just typed is not recoverable.

## Also this session

- **ftower was a pre-history-rewrite clone** — same "Initial commit" message and
  date as origin, different hash, 88 commits of its own lineage, so every pull
  died on "refusing to merge unrelated histories". Its `plugins/` registry had
  been *copied from the laptop*: every `installLocation` read
  `/Users/farishijazi/...`, and 1833 files under it were owned by root from a
  `sudo claude` run. Rebuilt from the tracked declaration after tagging the old
  head (`pre-rewrite-backup-20260915`) and preserving the 13 files that exist
  only there. This is the failure mode `plugins-mcp-and-connectors.md` warns
  about, seen in the wild.
- **Vendored upstream docs are now excluded from markdownlint and codespell.**
  Learned the hard way: running `markdownlint --fix` over the excalidraw skill
  renumbered a continuous 1–20 review checklist into several lists that each
  restart at 1, changing what the skill says. Committed, pushed, then restored
  from an untouched copy on ftower. Do not lint what you do not own.
