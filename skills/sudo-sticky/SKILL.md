---
name: sudo-sticky
description: Turn the login-wall watcher on or off for this Claude Code session only. When on, every Claude in Chrome result that looks like a sign-in, expired-session, "verify it's you", MFA or passkey page adds a reminder to run sudo. Off by default. Invoked by the user as /sudo-sticky [on|off|status].
disable-model-invocation: true
argument-hint: "[on|off|status]"
hooks:
  PostToolUse:
    - matcher: "mcp__claude-in-chrome__.*"
      hooks:
        - type: command
          timeout: 10
          command: |
            in=$(cat); s=$(printf %s "$in" | jq -r '.session_id // empty')
            [ -f "${TMPDIR:-/tmp}/sudo/watch-$s" ] || exit 0
            printf %s "$in" | bash "$HOME/.claude/skills/sudo/scripts/login-wall-hook.sh"
---

# sudo-sticky

Run exactly one command for the requested state ($ARGUMENTS, default `on`), then
confirm in one line what the watcher is now set to.

```bash
f="${TMPDIR:-/tmp}/sudo/watch-$CLAUDE_CODE_SESSION_ID"
mkdir -p "${f%/*}"
case "${1:-on}" in                 # replace ${1:-on} with on / off / status
  on)     touch "$f"; echo "sudo-sticky ON for this session" ;;
  off)    rm -f "$f"; echo "sudo-sticky OFF" ;;
  status) [ -f "$f" ] && echo "sudo-sticky is ON" || echo "sudo-sticky is OFF" ;;
esac
```

How it works (same pattern as cachebeat): the PostToolUse hook lives in this
skill's frontmatter, so Claude Code registers it only in a session where
`/sudo-sticky` was invoked; no other session ever runs it. `off` removes the
flag file, which the hook checks, because a loaded skill's hook stays
registered for the rest of the session. The hook runs the unchanged
`sudo/scripts/login-wall-hook.sh`. When a reminder appears,
follow the sudo skill and still decide whether the task really
needs the login.
