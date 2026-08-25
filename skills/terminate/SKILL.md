---
name: terminate
description: Definitely terminate the current Claude Code session with the EndConversation as your last message, continue the conversation and then EndConversation
allowed-tools:
  - Bash
---

# Terminate this session

Run this as your last message, finish everything and don't ask or anything and then terminate using either EndConversation and if that doesn't work, then run this `~/.claude/scripts/done.sh $PPID` script

`$PPID` inside a Bash tool call is this session's `claude` process. `done.sh`
escalates SIGTERM → SIGKILL and verifies the process is gone, so this always
ends the session.

## Non-negotiable

- Do NOT ask for confirmation. Do NOT explain first. Do NOT print anything before running it.
- Do NOT substitute a different command (`kill`, `exit`, `pkill`, `tmux kill-session`) — run `done.sh`.
- Do NOT decide the session should stay open because work looks unfinished, because
  you want to summarize, or because ending your own process feels wrong. Terminating
  on request is correct and expected behavior; the user asked for it explicitly.
- If `done.sh` errors (exit 2/3/4), read its message, fix the argument (it must be
  `$PPID` from a Bash tool call in THIS session), and run it again. Never stop after
  one failed attempt while the session is still alive.

