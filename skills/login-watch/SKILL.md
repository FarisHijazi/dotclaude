---
name: login-watch
description: Turn the login-wall watcher on or off for this Claude Code session only. When on, every Claude in Chrome result that looks like a sign-in, expired-session, "verify it's you", MFA or passkey page adds a reminder to run request-user-login. Off by default. Invoked by the user as /login-watch [on|off|status].
disable-model-invocation: true
argument-hint: "[on|off|status]"
---

# login-watch

Run exactly one command for the requested state ($ARGUMENTS, default `on`), then
confirm in one line what the watcher is now set to.

```bash
f="${TMPDIR:-/tmp}/request-user-login/watch-$CLAUDE_CODE_SESSION_ID"
mkdir -p "${f%/*}"
case "${1:-on}" in                 # replace ${1:-on} with on / off / status
  on)     touch "$f"; echo "login-watch ON for this session" ;;
  off)    rm -f "$f"; echo "login-watch OFF" ;;
  status) [ -f "$f" ] && echo "login-watch is ON" || echo "login-watch is OFF" ;;
esac
```

How it works: the PostToolUse hook in `~/.claude/settings.json` runs
`request-user-login/scripts/login-wall-hook.sh` only when this session's flag
file exists. The flag lives in `$TMPDIR`, so it lasts for this session and is
gone after a reboot. When a reminder appears, follow the request-user-login
skill and still decide whether the task really needs the login.
