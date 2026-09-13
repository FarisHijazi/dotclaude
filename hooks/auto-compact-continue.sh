#!/usr/bin/env bash
# Auto-compact a Claude Code session when its context fills up, then tell it to
# continue. Registered on Stop + PostCompact in settings.json; documented for
# users in commands/auto-compact.md (KEEP THE TWO IN SYNC).
#
#   Stop:                  used% >= threshold  -> type /compact
#   PostCompact trigger=manual -> type "continue ..."
#   PostCompact trigger=auto   -> nothing
#
# Why the trigger split: Claude Code's OWN auto-compaction fires mid-turn and
# resumes by itself, so nudging it would queue a spurious extra prompt. A
# *manual* /compact — whether we typed it or the user did — leaves the session
# sitting idle, and that is the case worth continuing. (`trigger` is the
# documented PostCompact matcher: "manual" | "auto".)
#
# Threshold: --set <pct> per tmux session > $AUTO_COMPACT_THRESHOLD > THR_DEFAULT.
# 0 or '' disables both halves. --force compacts now regardless.
#
# SAFETY: everything is typed into the pane with `tmux send-keys`, so it may only
# be sent when the Claude Code input box is EMPTY — otherwise "/compact" is
# appended to whatever the user is mid-way through typing and submitted with it.
# No hook/env/API exposes unsubmitted input, so the box is read off the screen
# with cc-prompt-state (from the cc-notify plugin). If it can't be read we do
# nothing: a missed compaction is recoverable, a mangled message is not.
#
# Requires: tmux, cc-prompt-state (on $PATH or via $CC_PROMPT_STATE).
set -uo pipefail

THR_DEFAULT=45
TMP="${TMPDIR:-/tmp}"; TMP="${TMP%/}"
me="${0##*/}"

# Typing the text and pressing Enter are two separate keystrokes and the TUI
# needs a beat between them: as "/compact" lands Claude Code redraws the input
# row and opens the slash-command menu, and an Enter that arrives mid-redraw is
# swallowed. ENTER_DELAY is that pause; CONFIRM_SECS is how long afterwards the
# input row is watched to prove the text really left it.
ENTER_DELAY="${AUTO_COMPACT_ENTER_DELAY:-1}"
CONFIRM_SECS="${AUTO_COMPACT_CONFIRM_SECS:-10}"

MARK=$'\342\235\257'   # U+276F  the prompt marker Claude Code draws
NBSP=$'\302\240'        # U+00A0  see still_typed()

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" >>"$TMP/cc-autocompact.log"; }
die() { echo "$me: $*" >&2; exit 2; }

usage() {
  cat >&2 <<USAGE
usage: $me [--force] [--set <pct>|--unset|--show] [--session <tmux-session>]

  --force            compact now, ignoring the threshold (self-trigger)
  --set <pct>        auto-compact this session at <pct>% context used (0 = never)
  --unset            drop the per-session setting (back to \$AUTO_COMPACT_THRESHOLD / $THR_DEFAULT)
  --show             print the effective threshold and where it comes from
  --session <name>   act on another tmux session instead of the current one
USAGE
  exit 2
}

force=0 action='' want_pct='' want_sess=''
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force|--skip-check) force=1 ;;
    --set)     action='set'; want_pct="${2:-}"; shift ;;
    --unset)   action='unset' ;;
    --show)    action='show' ;;
    --session) want_sess="${2:-}"; shift ;;
    *) usage ;;
  esac
  shift
done

# Per-session threshold file, keyed by tmux session name — the granularity the
# hook already works at (it types into `-t <session>`). Unlike the env var it can
# be changed while the session is running.
thr_file() { printf '%s/cc-ac-threshold-%s' "$TMP" "$(printf '%s' "$1" | tr -c 'A-Za-z0-9_.-' '_')"; }

# tmux session name: $1 if given, else the one holding $TMUX (socket,pid,$id).
resolve_sess() {
  command -v tmux >/dev/null || return 1
  if [[ -n "${1:-}" ]]; then
    tmux has-session -t "$1" 2>/dev/null || return 1
    printf '%s' "$1"; return 0
  fi
  [[ -n "${TMUX:-}" ]] || return 1
  local id="${TMUX##*,}"
  tmux display-message -t "\$${id#\$}" -p '#S' 2>/dev/null
}

threshold_for() {  # per-session file > env var > default
  local f; f=$(thr_file "$1")
  if   [[ -r "$f" ]];                          then cat "$f"
  elif [[ -n "${AUTO_COMPACT_THRESHOLD:-}" ]]; then printf '%s' "$AUTO_COMPACT_THRESHOLD"
  else                                              printf '%s' "$THR_DEFAULT"; fi
}

if [[ -n "$action" ]]; then
  if ! sess=$(resolve_sess "$want_sess"); then
    [[ -n "$want_sess" ]] && die "no such tmux session: $want_sess"
    die "not inside tmux — pass --session <name>"
  fi
  f=$(thr_file "$sess")
  case "$action" in
    set)
      [[ "$want_pct" =~ ^[0-9]+$ && "$want_pct" -le 100 ]] || die "--set needs a whole number 0-100"
      printf '%s\n' "$want_pct" >"$f"
      if [[ "$want_pct" == 0 ]]; then echo "auto-compact disabled for '$sess'"
      else echo "auto-compact for '$sess' set to ${want_pct}% context used"; fi ;;
    unset)
      rm -f "$f"; echo "auto-compact for '$sess' back to $(threshold_for "$sess")%" ;;
    show)
      if   [[ -r "$f" ]];                          then echo "'$sess': $(cat "$f")% (set for this session)"
      elif [[ -n "${AUTO_COMPACT_THRESHOLD:-}" ]]; then echo "'$sess': ${AUTO_COMPACT_THRESHOLD}% (from \$AUTO_COMPACT_THRESHOLD)"
      else                                              echo "'$sess': ${THR_DEFAULT}% (default)"; fi ;;
  esac
  exit 0
fi

# ---- hook path (or --force from inside a session) ----------------------------

if [[ "$force" == 1 ]]; then
  event=Stop                              # self-triggered: no hook JSON on stdin
  trigger=manual
  sid="${CLAUDE_CODE_SESSION_ID:-}"
else
  input=$(cat || true)
  json_str() { printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1; }
  event=$(json_str hook_event_name)
  trigger=$(json_str trigger)
  sid=$(json_str session_id)
fi
[[ -n "$sid" ]] || exit 0
sess=$(resolve_sess "") || exit 0          # not in tmux / no tmux → nothing to type into

# cc-prompt-state: explicit override, then $PATH, then the newest plugin-cache
# copy (any marketplace), then a local dev checkout. Never hardcode a version.
find_prompt_state() {
  [[ -n "${CC_PROMPT_STATE:-}" ]] && { printf '%s' "$CC_PROMPT_STATE"; return; }
  command -v cc-prompt-state 2>/dev/null && return
  local best='' f
  shopt -s nullglob
  for f in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/cache/*/cc-notify/*/bin/cc-prompt-state \
           "$HOME"/Projects/cc-notify/bin/cc-prompt-state; do
    [[ -x "$f" && ( -z "$best" || "$f" -nt "$best" ) ]] && best="$f"
  done
  shopt -u nullglob
  printf '%s' "$best"
}
prompt_state=$(find_prompt_state)

# cc-notify ships the pane type-lock next to cc-prompt-state. Its cc-color-apply
# hook types `/color <name>` into this very pane, and PostCompact fires both at
# the same instant: unserialised, the box ends up holding
# '/color bluecontinue and complete all tasks...' and BOTH abort, so neither is
# ever submitted. Absent (no cc-notify) → no-op stubs, unchanged behaviour.
lock_lib="$(dirname "$prompt_state")/cc-type-lock.sh"
# shellcheck source=/dev/null
[[ -r "$lock_lib" ]] && . "$lock_lib"
declare -F cc_type_lock >/dev/null || { cc_type_lock() { :; }; cc_type_unlock() { :; }; }

# cc-prompt-state, with the input row's padding treated as the whitespace it is.
#
# Claude Code separates the "❯" marker from the text with U+00A0, and an EMPTY
# row is exactly "❯" + U+00A0 and nothing else. cc-prompt-state trims with
# [[:space:]], which matches U+00A0 on macOS but NOT under glibc — so on the
# Debian boxes an empty box read as "the user is typing" (one U+00A0 of
# "text"), and a typed line came back with a leading U+00A0 that could never
# equal what we typed. Same script, same session, opposite verdicts by OS.
#
#   stdout: the box text, U+00A0 folded to a space and trimmed
#   return: 0 = empty, 1 = holds text, 2 = no input box on screen
read_box() {
  local t rc
  t=$("$prompt_state" "$1" 2>/dev/null); rc=$?
  [[ "$rc" -eq 2 ]] && return 2
  t="${t//$NBSP/ }"
  t="${t#"${t%%[![:space:]]*}"}"
  t="${t%"${t##*[![:space:]]}"}"
  printf '%s' "$t"
  [[ -z "$t" ]]
}

# Wait briefly for the input box to be readable AND empty (cc-prompt-state exit
# 0). Straight after a compaction the pane is still redrawing and has no box at
# all (exit 2), so a single probe would abandon a session that is a moment away
# from being perfectly safe. Worst case ~2.4s. Together with ENTER_DELAY and
# CONFIRM_SECS a stuck send costs ~14s, which is why settings.json gives this
# hook a 20s timeout rather than the stock 5s.
box_empty() {
  local i
  for ((i = 0; i < 8; i++)); do
    read_box "$sess" >/dev/null 2>&1 && return 0
    sleep 0.3
  done
  return 1
}

# Is $2 STILL sitting unsent in the input row of pane $1?
#
# Two details make this exact, both read off a live session:
#   * the UNSENT input row is "❯" + U+00A0 + text, while the transcript echo of
#     an already-SUBMITTED line is "❯" + an ordinary space — so the
#     non-breaking space is precisely what separates "waiting" from "gone";
#   * only the bottom of the pane is looked at, so the same line further up the
#     scrollback cannot match. 12 rows, not 4: the input row can wrap onto two
#     lines in a narrow `tw` pane and Claude Code draws two or three status
#     rows under the box.
# Matching a prefix rather than the whole string is the other half of surviving
# that wrap.
still_typed() {
  tmux capture-pane -p -t "$1" 2>/dev/null | tail -12 |
    grep -qF -- "$MARK$NBSP${2:0:24}"
}

# Keep pressing Enter while $1 is still sitting in the input row, for up to
# CONFIRM_SECS. The first Enter does not always take — it can arrive while
# Claude Code is still opening the slash-command menu — and then nothing is
# submitted, the context never shrinks, and the next Stop hits the same wall.
# Returns as soon as the row clears. still_typed is its own dialog guard: a
# permission dialog covers the input row, so our text cannot be seen there.
confirm_submitted() {
  local want="$1" deadline n=0
  deadline=$(( $(date +%s) + CONFIRM_SECS ))
  while :; do
    sleep 0.5
    if ! still_typed "$sess" "$want"; then
      [[ "$n" -gt 0 ]] && log "$sess: '$want' went through after $n extra Enter(s)"
      return 0
    fi
    [[ $(date +%s) -ge "$deadline" ]] && return 1
    tmux send-keys -t "$sess" Enter
    n=$(( n + 1 ))
  done
}

# Type $1 into the pane and submit it — only into an empty input box.
# One pane, one typist: hold the lock across the whole check-type-verify dance.
send() {
  local rc
  cc_type_lock "$sess" || { log "$sess: SKIP — another hook holds the pane type-lock"; return 1; }
  send_locked "$1"; rc=$?
  cc_type_unlock
  return "$rc"
}

send_locked() {
  local want="$1" cur rc
  [[ -x "$prompt_state" ]] || { log "$sess: ABORT no cc-prompt-state (cannot verify the box is empty)"; return 1; }
  box_empty || { log "$sess: SKIP box not empty / not present — user is typing or a dialog is open"; return 1; }
  tmux send-keys -t "$sess" -l -- "$want"
  sleep "$ENTER_DELAY"

  # The user can start typing between the check and now, so confirm the box
  # holds what we typed before pressing Enter. On mismatch abort WITHOUT
  # backspacing: our text sits there unsent (harmless), whereas blind
  # backspaces would eat the characters they just typed.
  cur=$(read_box "$sess"); rc=$?
  if [[ "$rc" -eq 2 ]]; then
    # No input box on screen at all — a permission dialog or a menu owns it.
    # Enter would answer THAT, so never press it.
    log "$sess: ABORT before Enter — no input box (dialog/menu on screen)"
    return 1
  fi
  if [[ "$rc" -eq 1 && "$cur" != "$want" ]]; then
    log "$sess: ABORT before Enter — box is '$cur', expected '$want'"
    return 1
  fi
  # rc 0 means the box reads EMPTY, which does NOT mean our text is missing:
  # cc-prompt-state drops coloured runs as decoration, and Claude Code colours a
  # RECOGNISED slash command (ESC[38;5;153m/compact), so '/compact' always reads
  # back as ''. That one line silently defeated every threshold compaction on
  # every machine — the log is full of "box is '', expected '/compact'". The raw
  # input row is the honest reading, so check that before giving up.
  if ! still_typed "$sess" "$want"; then
    log "$sess: ABORT before Enter — '$want' never reached the input row"
    return 1
  fi
  tmux send-keys -t "$sess" Enter
  log "$sess: sent '$want'"
  confirm_submitted "$want" ||
    log "$sess: WARNING '$want' STILL in the input row after ${CONFIRM_SECS}s"
}

mtime() {  # epoch seconds; GNU stat then BSD stat, 0 if neither works
  local t
  t=$(stat -c %Y "$1" 2>/dev/null) || t=$(stat -f %m "$1" 2>/dev/null) || t=0
  [[ "$t" =~ ^[0-9]+$ ]] || t=0
  printf '%s' "$t"
}

enabled() { local t; t=$(threshold_for "$1"); [[ -n "$t" && "$t" != 0 ]]; }

pending="$TMP/cc-ac-pending-$sid"          # debounces the Stop path only

case "$event" in
  Stop)
    if [[ "$force" == 0 ]]; then
      thr=$(threshold_for "$sess")
      [[ -n "$thr" && "$thr" != 0 ]] || exit 0
      m="$TMP/claude-ctx-$sid.json"       # written by cc-notify's context meter
      [[ -f "$m" ]] || exit 0
      used=$(sed -n 's/.*"used_pct"[[:space:]]*:[[:space:]]*\([0-9.]*\).*/\1/p' "$m" | head -1)
      [[ -n "$used" && "${used%%.*}" -ge "${thr%%.*}" ]] || exit 0
    fi
    # Skip only while a compact we triggered is still in flight (<2 min); stale → retry.
    if [[ -e "$pending" ]]; then
      (( $(date +%s) - $(mtime "$pending") < 120 )) && exit 0
      rm -f "$pending"
    fi
    : >"$pending"
    # Nothing submitted (user typing / dialog open) → drop the marker so the next
    # Stop retries instead of leaving a 2-minute dead window.
    send '/compact' || rm -f "$pending"
    ;;
  PostCompact)
    rm -f "$pending"                       # a compaction happened: unblock Stop
    # Continue after ANY manual /compact, not just ours: the session is idle
    # either way, and the whole point is that context pressure never stops work.
    if [[ "$trigger" == auto ]]; then
      log "$sess: PostCompact trigger=auto — Claude resumes on its own, not typing"; exit 0
    fi
    enabled "$sess" || { log "$sess: PostCompact but auto-compact is disabled here"; exit 0; }
    send 'continue and complete all tasks the user asked for'
    ;;
esac
exit 0
