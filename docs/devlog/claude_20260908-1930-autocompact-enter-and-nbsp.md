# Auto-compact typed `/compact` and never pressed Enter — two bugs, one row of text

2026-09-08. Report: "it runs compact but the enter button doesn't seem to send."
Correct, and it had never worked: `$TMPDIR/cc-autocompact.log` on all three
machines is a run of

```text
ABORT before Enter — box is '', expected '/compact'
```

Builds on @claude_20260901-1535-claudemd-slim-and-autocompact-portable.md.

## What the input row actually looks like

Measured on a throwaway `tmux -L actest` server running a real `claude`, with a
`tmux` shim on PATH so `cc-prompt-state` reads that server. `capture-pane -e`:

```text
ESC[39m ❯ U+00A0 ESC[38;5;153m /compact ESC[39m
```

Three facts fall out of that one line, and each is a bug:

1. **A recognised slash command is COLOURED** (`38;5;153`). `cc-prompt-state`
   deliberately drops coloured runs as decoration — that rule exists so the
   inline prompt suggestion and the placeholder hint are not mistaken for typed
   input. So `/compact` reads back as `''`, the `cur == want` guard fails, and
   the hook aborts with the text sitting unsent in the box. Every time.
2. **The marker and the text are separated by U+00A0**, not a space. Any check
   built on `❯ <text>` silently never matches.
3. **An EMPTY row is exactly `❯` + U+00A0.** `cc-prompt-state`'s trim uses
   `[[:space:]]`, which matches U+00A0 on macOS but **not** under glibc — so on
   the Debian boxes an empty box reported "the user is typing" (one U+00A0 of
   "text") and typed text came back with a leading U+00A0 that could never equal
   what we typed. Same script, same session, opposite verdicts by OS:

   ```text
   macOS   empty box -> rc 0, ''
   Debian  empty box -> rc 1, '<U+00A0>'
   ```

## The three changes

- **`read_box()`** wraps `cc-prompt-state` and folds U+00A0 to a space before
  trimming, so *this* script's notion of "empty" is the same on both OSes.
  `box_empty` and the pre-Enter check both go through it.
- **`still_typed()`** answers "is my text still sitting there unsent" off the
  RAW pane, because the colour-filtered reading structurally cannot see a slash
  command. The discriminator is the non-breaking space: the unsent input row is
  `❯`+U+00A0+text, while the transcript echo of an already-submitted line is
  `❯`+ordinary space (`e2 9d af 20`). Only the bottom 12 rows are searched, and
  a 24-char prefix is matched, so a wrapped row in a narrow `tw` pane still hits.
- **`confirm_submitted()`** — the half the user asked for. After Enter it polls
  that row for `CONFIRM_SECS` (10s, `$AUTO_COMPACT_CONFIRM_SECS`) and presses
  Enter again for as long as the text is there; `ENTER_DELAY` (1s,
  `$AUTO_COMPACT_ENTER_DELAY`) is a new pause *before* the first Enter so it
  cannot arrive while Claude Code is still opening the command menu. It is its
  own dialog guard: a permission dialog covers the input row, so our text cannot
  be seen there and no blind Enter is ever sent.

The pre-Enter verdict is now three-way rather than string equality: rc 2 (no
input box — a dialog owns the screen) aborts, rc 1 with different text aborts,
and rc 0 falls through to `still_typed`, which is the honest reading.

Worst case the hook now costs ~14s (2.4 box_empty + 1 delay + 10 confirm), so
`settings.json` gives it **20s** instead of the stock 5 on both Stop and
PostCompact — otherwise the confirmation loop would be killed mid-flight.

`THR_DEFAULT` is **40** (was 70), as asked.

## Tested

Isolated `tmux -L actest` server + a real `claude`, on **macOS and on thmanyah**,
driving the real hook through `run-shell` exactly as Claude Code does:

| check | macOS | thmanyah |
| --- | --- | --- |
| clean box → `/compact` submitted (transcript line count +1) | yes | yes |
| log says `sent '/compact'` with no WARNING | yes | yes |
| user mid-typing → `SKIP`, their text untouched | yes | yes |
| trust dialog on screen → `SKIP`, nothing typed, dialog intact | — | yes |
| `read_box` on empty / `/compact` / plain text | 0 '' / 0 '' / 1 'plain text here' | identical |
| PostCompact `trigger=manual` → continue message submitted | yes | — |
| PostCompact `trigger=auto` → nothing typed | yes | — |

Unit tests of the two new helpers against a fake box (`stty -echo` so Enter
cannot scroll it): `confirm_submitted` recovered a swallowed Enter in one retry
and logged `went through after 1 extra Enter(s)`; against a box that never
clears it returned 1 after exactly 10s.

`shellcheck -x` clean apart from the four pre-existing SC1007/SC2209 notes.

## Trap for the next person

`--force` writes `$TMPDIR/cc-ac-pending-<sid>` and the Stop path skips for 2
minutes while that marker is fresh. Two consecutive manual test runs therefore
look like "the fix did nothing" — delete the marker between runs.

## Addendum (20:15) — the hook is not the only typist

The first live PostCompact after the fix logged
`ABORT before Enter — box is 'bluecontinue and complete all tasks the user asked
for'`. The stray `blue` is cc-notify's `cc-color-apply.sh` typing `/color blue`
into the same pane on SessionStart: PostCompact fires both hooks at the same
instant, they interleave inside each other's check-type-verify dance, and both
correctly refuse to press Enter because neither reads back what it typed. Net
effect: nothing is ever submitted and a colour word is left in the box.

`send()` is now a wrapper that holds cc-notify's `bin/cc-type-lock.sh` (a
mkdir-lock keyed on `#{pane_id}`, found next to `cc-prompt-state`) across the
whole of `send_locked()`. If cc-notify isn't installed the lock resolves to
no-op stubs and behaviour is unchanged.

Proven with three typists racing into one live Claude pane — `/color purple`
(SessionStart), `/color blue`, `/compact` — all three applied in sequence.

Test trap: `--force` resolves its session from `$TMUX`, which must be faked as
`<socket_path>,<server_pid>,<session_id>`; a bogus socket path makes
`resolve_sess` return empty and the hook exits 0 silently.
