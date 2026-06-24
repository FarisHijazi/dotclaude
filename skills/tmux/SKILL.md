---
name: tmux
description: Observe and control tmux sessions — list sessions (local and on remote SSH machines), read and search their pane text including scrollback that has scrolled off-screen, and send keystrokes. Use to peek at what other Claude Code / shell sessions are doing, find a line that scrolled away, check on long-running jobs, or drive an interactive TUI in another pane. Triggers: "what's that other tmux session doing", "read the other claude", "list my tmux sessions", "search the scrollback", "check the worker pane", "send keys to session X".
---

# tmux session observation & control

Every Claude Code here runs inside a tmux session, so any session can read and
drive any other session's text via the `tmux` CLI (through the Bash tool). This
skill is the bridge: **list → read/search → (optionally) send keys.**

Primary jobs, in priority order:
1. **List** sessions — local AND on remote SSH machines.
2. **Read & search** a session's text, including scrollback that is NOT
   currently visible on screen (scrolled off the top).
3. **Send keystrokes** to a session (text, Enter, control keys).

`capture-pane -p` prints to stdout — that `-p` is what makes everything below
scriptable. Target format is `session:window.pane` (e.g. `mysess:0.0`);
`session` alone targets its active pane.

## How these sessions are created (naming you'll see)

Claude Code sessions here are launched by the `tcc()` shell function (see
@~/.bash_aliases) — one Claude per tmux session. Knowing the scheme lets you
identify a session two ways:

- **Session name = the project.** `tcc` names the session `<cwd-basename>-<N>`,
  where `<N>` is the next free index (`farishijazi-1`, `control-service-2`, …).
  `.`/`:` in the dir name become `_` (tmux forbids them). So the name tells you
  *which repo/dir* the agent is working in, not what it's doing. `tcc` refuses
  to run inside an existing `$TMUX`, so nesting never happens.
- **Pane title = what it's doing.** Claude Code sets the tmux `pane_title` to its
  current *conversation title* (e.g. `fixing basecampcoach`, `ramp rate`). This
  is the best signal for the task a session is on. Read it without capturing the
  pane:

  ```bash
  tmux list-panes -a -F '#{session_name}  ❯ #{pane_title}  [#{pane_current_command}]'
  ```

  Find the session working on a topic:

  ```bash
  # (tmux -F does NOT expand \t — use a literal separator like ' :: ')
  tmux list-panes -a -F '#{session_name} :: #{pane_title}' | grep -i 'ramp rate'
  ```
- **Status-bar color** is just a hash of the working dir (set by `tcc` /
  re-synced by @~/.claude/hooks/gsd-statusline.js) — cosmetic, for telling
  projects apart at a glance; not something to script against.

`pane_current_command` shows the claude binary version (e.g. `2.1.187`) while a
session is live — a quick "is this actually a Claude Code session" check.

---

## 1. List sessions

### Local

```bash
tmux ls                                   # one line per session
tmux list-sessions -F '#{session_name}'   # just the names (script-friendly)
tmux list-windows  -t <session>           # windows in a session
tmux list-panes    -t <session> -a        # every pane, all sessions
```

Do NOT hardcode session names — they vary (`<project>-1`, `<project>-2`, …).
Always discover them with `tmux ls` first, then loop over the result.

### Remote (sessions on other SSH machines)

tmux is per-host: `tmux ls` on this Mac only shows local sessions. To see a
session running on another box, run tmux **over SSH**. Hosts come from
`~/.ssh/config` — list them with:

```bash
grep -iE '^Host ' ~/.ssh/config | awk '{print $2}' | grep -v '[*?]'
```

Then query a specific host (replace `<host>` with one of those):

```bash
ssh <host> tmux ls 2>/dev/null            # sessions on that machine
```

Sweep every configured host at once (skips hosts that are down / have no tmux):

```bash
for h in $(grep -iE '^Host ' ~/.ssh/config | awk '{print $2}' | grep -v '[*?]'); do
  out=$(ssh -o ConnectTimeout=4 -o BatchMode=yes "$h" 'tmux ls 2>/dev/null')
  [ -n "$out" ] && printf '\n=== %s ===\n%s\n' "$h" "$out"
done
```

Notes:
- `-o ConnectTimeout=4` keeps unreachable hosts from hanging the sweep.
- `-o BatchMode=yes` skips hosts that would prompt for a password (no hang).
- If a host's tmux runs under a different user, SSH as that user in `~/.ssh/config`.

---

## 2. Read & search pane text (incl. off-screen scrollback)

`capture-pane -p` defaults to the **visible** region only. To reach text that
has scrolled off the top, add `-S` (start line) / `-E` (end line). `-S -` means
"from the very beginning of the scrollback buffer."

```bash
# Visible region only
tmux capture-pane -t <session> -p

# Last 40 visible lines
tmux capture-pane -t <session> -p | tail -40

# ENTIRE scrollback (everything that ever scrolled past, top to bottom)
tmux capture-pane -t <session> -p -S -

# A bounded window of history: 500 lines back up to the current bottom
tmux capture-pane -t <session> -p -S -500

# A specific pane
tmux capture-pane -t <session>:0.1 -p -S -
```

By default the scrollback buffer holds ~2000 lines (the `history-limit`
option). Lines older than that are gone — `-S -` returns as much as the buffer
retained, not infinitely far back.

### Search the scrollback (find a line that scrolled away)

Capture full history, then grep — this is how you find something no longer on
screen:

```bash
# Find error lines anywhere in this session's history
tmux capture-pane -t <session> -p -S - | grep -niE 'error|traceback|fail'

# Show 3 lines of context around each match
tmux capture-pane -t <session> -p -S - | grep -niE 'exception' -A3 -B1
```

### Search across ALL local sessions at once

```bash
for s in $(tmux list-sessions -F '#{session_name}'); do
  hit=$(tmux capture-pane -t "$s" -p -S - | grep -niE 'PATTERN')
  [ -n "$hit" ] && printf '\n=== %s ===\n%s\n' "$s" "$hit"
done
```

### Read / search a remote session's text

Same `capture-pane`, just over SSH. Quote the remote command so flags reach the
remote tmux, not local SSH:

```bash
ssh <host> 'tmux capture-pane -t <session> -p -S -'                 # full history
ssh <host> 'tmux capture-pane -t <session> -p -S - | grep -niE "error"'
```

### Peek at every local session (status glance)

```bash
for s in $(tmux list-sessions -F '#{session_name}'); do
  echo "=== $s ==="
  tmux capture-pane -t "$s" -p | tail -6
done
```

---

## 3. Send keystrokes  (secondary — use with care)

> Sending keys *acts* inside another live session. Read the pane first
> (section 2) to confirm its state before typing, so you don't fire input into
> the wrong prompt. When in doubt, ask the user.

```bash
# Text only (does NOT press Enter)
tmux send-keys -t <session> "hello"

# Text + Enter
tmux send-keys -t <session> "y" Enter

# Special / control keys
tmux send-keys -t <session> Enter
tmux send-keys -t <session> Escape
tmux send-keys -t <session> C-c     # Ctrl+C
tmux send-keys -t <session> C-d     # Ctrl+D (EOF)
```

**Safe send for interactive TUIs** (Claude Code, REPLs, editors): send the text
literally with `-l --`, pause, then send Enter separately. This avoids
paste/multiline edge cases where the text and newline get merged or auto-run:

```bash
tmux send-keys -t <session> -l -- "Please apply the patch in src/foo.ts"
sleep 0.1
tmux send-keys -t <session> Enter
```

Remote send works the same over SSH (quote it):

```bash
ssh <host> 'tmux send-keys -t <session> "y" Enter'
```

### Common Claude-Code patterns

```bash
# Is a session waiting on a prompt?
tmux capture-pane -t <session> -p | tail -10 | grep -nE '❯|Yes.*No|proceed|permission|\(y/n\)'

# Approve a y/n prompt
tmux send-keys -t <session> 'y' Enter

# Pick a numbered option
tmux send-keys -t <session> '2' Enter
```

---

## Reference

| Need | Command |
| --- | --- |
| List local sessions | `tmux ls` |
| List remote sessions | `ssh <host> tmux ls` |
| Names only (scriptable) | `tmux list-sessions -F '#{session_name}'` |
| Visible text | `tmux capture-pane -t <s> -p` |
| Full scrollback | `tmux capture-pane -t <s> -p -S -` |
| Last N history lines | `tmux capture-pane -t <s> -p -S -<N>` |
| Search history | `tmux capture-pane -t <s> -p -S - \| grep -niE 'PAT'` |
| Remote read | `ssh <host> 'tmux capture-pane -t <s> -p -S -'` |
| Send text+Enter | `tmux send-keys -t <s> "txt" Enter` |
| Safe TUI send | `send-keys -l -- "txt"` → `sleep 0.1` → `send-keys Enter` |

Gotchas:
- `-p` is required to print to stdout; without it `capture-pane` writes to a
  paste buffer instead and you see nothing.
- `capture-pane` without `-S -` only sees the visible region — easy to miss
  output that already scrolled past. For "find what happened earlier," always
  use `-S -`.
- Over SSH, **quote** the whole remote `tmux …` command so pipes/flags run on
  the remote, not locally.
- History is capped by tmux's `history-limit` (default ~2000 lines); older
  output is unrecoverable.
