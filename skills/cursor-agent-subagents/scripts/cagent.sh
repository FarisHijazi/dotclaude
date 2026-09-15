#!/usr/bin/env bash
# cagent.sh — dispatch + monitor headless cursor-agent subagents (fire-and-forget).
# State per run lives in $CAGENT_RUNS/<name>/{log,pid,err,meta}
# Usage:
#   cagent.sh run <name> [-- extra cursor-agent flags --] "<prompt>"
#       env overrides: MODEL (default cursor-grok-4.5-high), MODE (ask|plan|agent*), WORKTREE, WORKSPACE
#   cagent.sh status <name>      -> one line: STATE <detail>
#   cagent.sh statusall          -> status of every run
#   cagent.sh result <name>      -> final result text (or tail of log)
#   cagent.sh sid <name>         -> session_id (for cursor-agent --resume)
# States: RUNNING STALLED DONE NEED_HELP FAILED OUT_OF_CREDITS BAD_MODEL CRASHED
set -u
RUNS="${CAGENT_RUNS:-$HOME/.cache/cagent-runs}"
STALL_SECS="${CAGENT_STALL_SECS:-300}"

die() { echo "cagent: $*" >&2; exit 2; }

cmd="${1:-}"; shift || true
case "$cmd" in
run)
  name="${1:?run name}"; shift
  extra=()
  if [ "${1:-}" = "--" ]; then
    shift
    while [ $# -gt 1 ]; do
      [ "$1" = "--" ] && { shift; break; }
      extra+=("$1"); shift
    done
  fi
  prompt="${1:?prompt}"
  d="$RUNS/$name"; mkdir -p "$d"
  [ -f "$d/pid" ] && kill -0 "$(cat "$d/pid")" 2>/dev/null && die "run '$name' already active"
  args=(-p --output-format stream-json --trust -f --model "${MODEL:-cursor-grok-4.5-high}")
  case "${MODE:-agent}" in ask|plan) args+=(--mode "${MODE}");; esac
  [ -n "${WORKTREE:-}" ] && args+=(--worktree "$WORKTREE")
  args+=(--workspace "${WORKSPACE:-$PWD}")
  [ ${#extra[@]} -gt 0 ] && args+=("${extra[@]}")
  printf '%s\n' "$prompt" > "$d/prompt"
  ( cursor-agent "${args[@]}" "$prompt" > "$d/log" 2> "$d/err"
    echo "$?" > "$d/exit" ) &
  echo "$!" > "$d/pid"
  echo "dispatched '$name' (pid $(cat "$d/pid")) -> $d"
  ;;
status)
  name="${1:?name}"; d="$RUNS/$name"
  [ -d "$d" ] || die "no such run: $name"
  pid=$(cat "$d/pid" 2>/dev/null || echo "")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    # alive: stalled if log hasn't grown recently
    now=$(date +%s); mt=$(stat -f %m "$d/log" 2>/dev/null || stat -c %Y "$d/log" 2>/dev/null || echo "$now")
    age=$(( now - mt ))
    if [ "$age" -gt "$STALL_SECS" ]; then echo "STALLED no log activity for ${age}s (pid $pid)"; else echo "RUNNING last activity ${age}s ago"; fi
    exit 0
  fi
  # dead: classify from log/err
  if grep -qiE 'usage limit|ActionRequiredError' "$d/err" 2>/dev/null; then
    echo "OUT_OF_CREDITS $(head -c 200 "$d/err" | tr '\n' ' ')"; exit 0; fi
  if grep -q 'Cannot use this model' "$d/err" 2>/dev/null; then
    echo "BAD_MODEL $(head -1 "$d/err" | cut -c1-120)"; exit 0; fi
  last=$(tail -1 "$d/log" 2>/dev/null)
  if printf '%s' "$last" | jq -e 'select(.type=="result")' >/dev/null 2>&1; then
    res=$(printf '%s' "$last" | jq -r .result)
    if printf '%s' "$last" | jq -e '.is_error==true' >/dev/null 2>&1; then
      echo "FAILED $(printf '%s' "$res" | head -c 160 | tr '\n' ' ')"
    elif printf '%s' "$res" | grep -q 'NEED_HELP:'; then
      echo "NEED_HELP $(printf '%s' "$res" | grep 'NEED_HELP:' | head -1)"
    else
      echo "DONE"
    fi
  else
    echo "CRASHED exit=$(cat "$d/exit" 2>/dev/null || echo '?') no result event; err: $(head -c 160 "$d/err" 2>/dev/null | tr '\n' ' ')"
  fi
  ;;
statusall)
  for d in "$RUNS"/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    printf '%-24s %s\n' "$n" "$("$0" status "$n")"
  done
  ;;
result)
  name="${1:?name}"; d="$RUNS/$name"
  tail -1 "$d/log" | jq -r 'select(.type=="result") | .result' 2>/dev/null || tail -5 "$d/log"
  ;;
sid)
  name="${1:?name}"; d="$RUNS/$name"
  grep -m1 '"subtype":"init"' "$d/log" | jq -r .session_id
  ;;
*)
  sed -n '2,12p' "$0"; exit 2
  ;;
esac
