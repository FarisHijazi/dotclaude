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
