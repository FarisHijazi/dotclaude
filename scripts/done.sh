#!/usr/bin/env bash
# done.sh — end a Claude Code session for good.
#
# Usage (from inside the session you want to end):
#     ~/.claude/scripts/done.sh $PPID
#
# $PPID inside a Bash tool call is the `claude` process itself, so passing it is
# how a session names itself. Escalates SIGTERM -> SIGKILL and verifies the
# process is actually gone, so a session cannot "decide" to stay alive.
#
# Exit codes: 0 killed (or already gone) | 2 bad usage | 3 not a claude pid | 4 survived

set -uo pipefail

die() { printf 'done.sh: %s\n' "$1" >&2; exit "$2"; }

pid=${1:-}
[ -n "$pid" ] || die "missing PPID. Usage: done.sh \$PPID (run it from inside the session to end)" 2
[[ $pid =~ ^[0-9]+$ ]] || die "'$pid' is not a pid. Usage: done.sh \$PPID" 2
[ "$pid" -gt 1 ] || die "refusing to signal pid $pid" 2

alive() { kill -0 "$pid" 2>/dev/null; }

# Already dead? Nothing to do — the session is over either way.
alive || { echo "done.sh: pid $pid is already gone"; exit 0; }

# Only ever kill a claude process owned by this user, so a wrong pid is loud
# rather than destructive.
cmd=$(ps -o command= -p "$pid" 2>/dev/null || true)
own=$(ps -o user= -p "$pid" 2>/dev/null | tr -d ' ')
case $cmd in
  *claude*) : ;;
  *) die "pid $pid is not a claude process (${cmd:-unknown}) — pass \$PPID from inside the session" 3 ;;
esac
[ "$own" = "$(id -un)" ] || die "pid $pid belongs to '$own', not $(id -un)" 3

echo "done.sh: terminating claude pid $pid"

# 1) Ask nicely, give it ~3s to flush state and exit.
kill -TERM "$pid" 2>/dev/null
for _ in $(seq 30); do alive || { echo "done.sh: pid $pid exited (SIGTERM)"; exit 0; }; sleep 0.1; done

# 2) It ignored us. Non-negotiable.
echo "done.sh: still alive after SIGTERM, sending SIGKILL"
kill -KILL "$pid" 2>/dev/null
for _ in $(seq 20); do alive || { echo "done.sh: pid $pid killed"; exit 0; }; sleep 0.1; done

die "pid $pid survived SIGKILL (unkillable/zombie state) — kill it manually" 4
