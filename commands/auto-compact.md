This skill is the user-facing half of the hook script
`~/.claude/hooks/auto-compact-continue.sh` — every command below is that script,
and it is registered on `Stop` + `PostCompact` in `~/.claude/settings.json`.
**The two are a pair: change the script's flags or defaults and update this file
in the same edit** (and vice versa). Design notes and test evidence:
`~/.claude/docs/devlog/claude_20260901-1535-claudemd-slim-and-autocompact-portable.md`.
(Referenced by path, not `@`-imported, so running this skill doesn't pull ~200
lines of bash into the context it exists to protect.)

Don't worry about the context limit at all — it auto-compacts. If you see the
context getting high, never let that stop you or cut work short: keep going.

**Never stop because context is filling up.**

If you genuinely need to compact right now, don't hand-roll it with tmux
send-keys — run this one line:

```bash
bash ~/.claude/hooks/auto-compact-continue.sh --force
```

That submits `/compact` into this session and, once it finishes, the
`PostCompact` hook automatically sends you "continue and complete all tasks the
user asked for" — so you pick straight back up. Both hooks are already
registered; you don't need to send anything yourself.

Why not to do it manually: typing `/compact` in with `tmux send-keys` appends it
to whatever the user is *currently typing* in their input box and submits their
half-written sentence along with it. The flag-based path checks the input box is
empty first, re-verifies immediately before pressing Enter, and refuses outright
if a menu or permission dialog is open.

Notes:

- Only works inside tmux (it exits silently otherwise).
- The continue message fires after **any manual compaction** — one this script
  typed, or one the user typed themselves. It deliberately does **not** fire
  after Claude Code's own built-in auto-compaction (hook `trigger` is `"auto"`),
  which happens mid-turn and resumes by itself; typing at that would queue a
  spurious extra prompt.
- If it declines (user mid-typing, dialog open), **that's correct** — it logs the
  reason to `$TMPDIR/cc-autocompact.log` and the next turn-end retries
  automatically. Don't work around it by typing into the pane yourself.
- Run it, then finish your current turn normally. The compact runs at the turn
  boundary, not mid-response.
- The auto-continue message is generic, so if there's task detail that must
  survive, write a short handoff note to a file first (e.g.
  `docs/devlog/...` or a scratch file) and mention the path — a file survives
  compaction far better than anything you type into the prompt.
- It also fires on its own at 70% context used by default, so most of the time
  you never need to think about this.

To change *when* it fires for one session (works on a session that's already
running, from inside it or from any other terminal):

```bash
H=~/.claude/hooks/auto-compact-continue.sh
bash $H --show                              # effective threshold + where it came from
bash $H --set 70                            # this session: compact at 70% used
bash $H --set 0                             # this session: never auto-compact
bash $H --set 70 --session <tmux-session>    # some other session, from outside
bash $H --unset                             # back to the default
```

Settings are keyed by **tmux session name** and beat `$AUTO_COMPACT_THRESHOLD`
(which can only be set when launching `claude`, and can't be changed afterwards).
`--set 0` disables **both** halves: no threshold compaction and no continue
message.
