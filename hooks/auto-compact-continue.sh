#!/usr/bin/env bash
# Stop: if used% ≥ AUTO_COMPACT_THRESHOLD → /compact
# PostCompact: if we triggered it → continue
# AUTO_COMPACT_THRESHOLD default 15; '' or 0 disables.
set -euo pipefail
[[ -z "${TMUX:-}" ]] && exit 0

input=$(cat || true)
event=$(printf '%s' "$input" | sed -n 's/.*"hook_event_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
sid=$(printf '%s' "$input" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
[[ -z "$sid" ]] && exit 0

# TMUX=socket,pid,$id — third field may or may not have a leading $
id="${TMUX##*,}"; id="${id#\$}"
sess=$(tmux display-message -t "\$$id" -p '#S' 2>/dev/null) || exit 0

send() {
  tmux send-keys -t "$sess" -l -- "$1"
  sleep 0.1
  tmux send-keys -t "$sess" Enter
}

# mtime in epoch seconds — GNU stat (Linux) then BSD stat (macOS). 0 if neither works.
mtime() {
  local t
  t=$(stat -c %Y "$1" 2>/dev/null) || t=$(stat -f %m "$1" 2>/dev/null) || t=0
  [[ "$t" =~ ^[0-9]+$ ]] || t=0
  printf '%s' "$t"
}

pending="${TMPDIR:-/tmp}/cc-ac-pending-$sid"

case "$event" in
  Stop)
    thr="${AUTO_COMPACT_THRESHOLD-40}"
    [[ -z "$thr" || "$thr" == 0 ]] && exit 0
    m="${TMPDIR:-/tmp}/claude-ctx-$sid.json"
    [[ -f "$m" ]] || exit 0
    used=$(sed -n 's/.*"used_pct"[[:space:]]*:[[:space:]]*\([0-9.]*\).*/\1/p' "$m" | head -1)
    [[ -z "$used" || "${used%%.*}" -lt "${thr%%.*}" ]] && exit 0
    # Only skip if a compact we triggered is still in flight (<2 min). Stale pending → retry.
    if [[ -e "$pending" ]]; then
      age=$(( $(date +%s) - $(mtime "$pending") ))
      [[ "$age" -lt 120 ]] && exit 0
      rm -f "$pending"
    fi
    : >"$pending"
    send '/compact'
    ;;
  PostCompact)
    [[ -e "$pending" ]] || exit 0
    rm -f "$pending"
    send 'continue'
    ;;
esac
exit 0
