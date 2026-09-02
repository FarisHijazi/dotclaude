# Slimmed CLAUDE.md into memories; made the auto-compact hook portable

Date: 2026-09-01

## 1. CLAUDE.md: 155 new lines → 25

Three long sections had been added to the global `CLAUDE.md` (always loaded, every
session). Split by *how often each is relevant*:

| Section | Destination | Rationale |
|---|---|---|
| NEVER kill by a broad pattern | stays in `CLAUDE.md`, 8 lines; incident detail → `memory/feedback_never_kill_by_pattern.md` | Must fire *before* a tool call. Memory recall is relevance-based and probabilistic, so the hard rule has to be always-loaded; the Proxmox war story does not. |
| Before you write a new thing, find who already owns it (60 lines) | `memory/feedback_find_the_owner_first.md`, 6-line pointer left in `CLAUDE.md` | Situational design guidance — only relevant when adding a write path/module. |
| Never render absent data as an answer (35 lines) | `memory/feedback_never_render_absent_data.md`, 4-line pointer left | Frontend-only; irrelevant to most sessions. |

Not turned into skills: a skill needs an invocation moment, and "I am about to add a
second writer" / "I am about to render a fetched list" are not moments anything can
trigger on. Memory recall keys off exactly that kind of description.

**Trap avoided:** the pointers use plain backticked paths, NOT `@memory/...`. In
`CLAUDE.md` the `@path` syntax *eagerly imports* the file, which would have loaded the
same tokens every session and made the split pointless.

Index lines added to `memory/MEMORY.md` (one per memory, per the memory conventions).

## 2. `hooks/auto-compact-continue.sh` — portability + simplification

139 → 182 lines by line count but the added lines are the extracted helpers; the
machine-specific parts are gone. Behaviour and safety semantics are unchanged.

What was wrong:
- **`cc-prompt-state` discovery hardcoded** a dev checkout path and the marketplace
  name `farishijazi-plugins`. It is already on `$PATH` via the plugin's bin dir.
  Now: `$CC_PROMPT_STATE` → `command -v` → `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/cache/*/cc-notify/*/bin/`
  (marketplace-agnostic glob, newest by mtime) → `$HOME/Projects/cc-notify/bin/`.
  Also replaced `$(ls -dt ...)` in a `for` (word-splits on spaces) with a nullglob loop
  using `-nt`.
- **Header cited a devlog that does not exist** (`~/docs/devlog/claude_20260803-1945-...`).
  Dropped, along with the `~/.claude/`-absolute paths in comments — the file lives in
  that dir, so repo-relative paths read the same on any machine.
- **Default threshold `70` was written in 4 places.** Now one `THR_DEFAULT=70` and one
  `threshold_for()` implementing the precedence (per-session file > env > default),
  used by both `--show`/`--unset` and the Stop check.
- **`${TMUX##*,}` session parsing duplicated** in two places → one `resolve_sess()`,
  which now also guards `command -v tmux` so a box without tmux exits 0 on the hook
  path (silent, correct) and prints a usable error on the CLI path.
- `TMPDIR` normalised once into `$TMP` (trailing slash stripped — macOS `$TMPDIR` has one).

Two bugs introduced during the rewrite and caught by the tests:
- `die "${want_sess:+no such session: $want_sess}${want_sess:-not inside tmux}"` —
  `:-` yields the *value* when the var is non-empty, so the message concatenated both
  halves. Replaced with an `if`.
- `AUTO_COMPACT_THRESHOLD= threshold_for "$sess"` — the `VAR=val func` form leaks the
  assignment in bash. Unneeded anyway: after `rm -f` the file, `threshold_for` already
  returns env-or-default.

## Test evidence

Two scripts, 24 assertions, all passing: CLI (`--show`/`--set`/`--unset` precedence,
bad pct, bad flag, missing session, outside tmux), hook Stop (no ctx file, above
threshold, below threshold, threshold 0), `--force` (ignores ctx file and a 0
threshold, no-op without a session id), PostCompact (with and without the pending
marker), stale-marker retry, `CC_PROMPT_STATE` override, and a PATH with no tmux.

**Testing hazard, learned the hard way:** the hook path resolves its target session
from `$TMUX`, so an above-threshold Stop test run *from inside a live Claude pane*
really does type `/compact` into that pane and press Enter — it did, into the session
running the test. Give every send-path test a stub `CC_PROMPT_STATE` that exits
non-zero (reports the box as non-empty); `send()` then aborts before typing and the
whole state machine is still exercised.

---

# Follow-up (16:00): the continue message never fired

## Symptom

A `/compact` ran in a live session, `PostCompact` ran ("completed successfully"),
and nothing was typed. The user had to hand-write "continue" — exactly the thing
the hook exists to avoid.

## Root cause

`PostCompact` was gated on a pending marker file that only the *Stop* half writes:

```bash
PostCompact)
  [[ -e "$pending" ]] || exit 0     # <- silently did nothing
```

So the continue message fired **only** after a compaction this script itself
triggered. Every other route to a compacted, idle session — the user typing
`/compact`, or an agent doing it — got nothing. `$TMP` held no marker at all
(verified: no `cc-ac-pending-*`, no log file), because the marker from the test
run went into an isolated `TMPDIR`, and the compaction that actually happened was
a manual one.

## Fix: gate on the hook's `trigger`, not on our own marker

`PreCompact`/`PostCompact` carry a documented matcher — `"manual"` or `"auto"`
(confirmed in the shipped binary's own hook reference: `| PostCompact |
"manual"/"auto" | After compaction (receives summary) |`). That is the correct
discriminator, and it is about the *session's state*, not about who triggered it:

| `trigger` | What happened | Session after | Action |
|---|---|---|---|
| `manual` | `/compact` was submitted (ours or the user's) | **idle, waiting** | type the continue message |
| `auto` | Claude Code's own built-in auto-compaction | mid-turn, resumes itself | nothing — typing would queue a spurious extra prompt |

An absent/unknown `trigger` falls through to the `manual` branch: continuing is
the useful default, and the empty-box guard makes it safe.

The pending marker keeps its one real job — debouncing the Stop path so a
second turn-end doesn't submit a second `/compact` — and `PostCompact` now
*clears* it (a compaction happened, so Stop is unblocked) instead of reading it.
`--set 0` disables both halves, which is the escape hatch for anyone who does
not want to be nudged after their own `/compact`.

## Second fix: the box isn't drawn yet right after a compaction

`send()` probed `cc-prompt-state` once. Straight after a compaction the pane is
still redrawing and has **no input box** (`cc-prompt-state` exit 2 — the same
"unsafe" answer it gives for a menu), so a single probe would have refused a
session that was a moment away from being perfectly safe. Replaced with
`box_empty()`: up to 8 probes, 0.3s apart (~2.4s worst case, inside the 5s hook
timeout registered in `settings.json`).

## Test evidence

`t3.sh`, 20 assertions, all passing — including the regression itself
("manual with no pending marker must still reach `send`"), `trigger=auto`
suppression, absent-`trigger` fallback, `--set 0` disabling the continue half,
the marker being cleared, Stop debounce/stale-retry, threshold precedence, and
the `box_empty` retry finishing in 2-4s. Send-path tests use the stub
`CC_PROMPT_STATE` trick from the section above, so nothing is typed anywhere.

## End-to-end, in a throwaway session

The state machine is unit-tested, but "does the box exist and read as empty when
`PostCompact` fires" can only be answered by a real compaction. Run in a
disposable `ac-e2e` tmux session (never the caller's — the hook resolves its
target from `$TMUX`). Two things that trip this up:

- A **fresh Claude session shows first-run dialogs** ("Teach auto mode about your
  environment?"). `cc-prompt-state` reported no input box and the hook refused to
  type — the safety guard behaving exactly as designed. Dismiss with `Escape`
  first.
- **`/compact` on a short conversation is refused** ("Not enough messages to
  compact") and then **no `PostCompact` fires at all**. The stale-marker retry
  already covers the marker left behind. A real test needs several exchanges
  first.

## The other reason it never fired: the input box was never "empty"

Trying to prove the fix end-to-end turned up a second, independent cause — and
this one is not in this repo. `cc-prompt-state` was reporting Claude Code's
greyed-out **inline prompt suggestion** as user input:

```
$ cc-prompt-state ac-e2e
Name one SQL keyword.        # exit 1 = "user is typing, do NOT send-keys"
```

Nothing had been typed. `send()` fails closed on exit 1 (correctly), so while a
suggestion or a placeholder hint is on screen, auto-compact is silently disabled
— no log line, no symptom, just nothing happening. Same for every other consumer
of that reader.

Fixed in the owner rather than worked around here (`cc-prompt-state` owns "read
the input box"; a second parser in this hook would be the exact duplication the
find-the-owner rule exists to prevent). Full write-up, including why "strip the
dim text" is the wrong fix — dim marks the box *borders* in some themes and the
*hint* in others — and the before/after table across all 7 live panes:
`~/Projects/cc-notify/docs/devlog/claude_20260901-1600-prompt-state-ignores-suggestions.md`. Shipped as cc-notify **v1.7.18**
(`claude plugin update cc-notify`; the marketplace tracks that repo's `main`, so
the push is the release).

`box_empty()`'s retry is still needed after that fix: it covers the pane being
mid-redraw (no box at all) right after a compaction, which is a different state
from "box has text".

## Still unproven

A real compaction driving a real `PostCompact` into a real typing attempt.
Blocked twice in the throwaway session: first-run dialogs (guard refused —
correct), then `/compact` refusing with "Not enough messages to compact" on a
short conversation, which fires **no `PostCompact` at all**. The remaining way to
prove it is `--force` in a session that has real history — i.e. a live one.
