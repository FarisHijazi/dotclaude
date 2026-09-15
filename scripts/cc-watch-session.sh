#!/usr/bin/env bash
# cc-watch-session.sh — babysit ANOTHER Claude Code tmux session so a long
# autonomous run doesn't die unattended.
#
#   cc-watch-session.sh <tmux-session> <expected-pane-title-substring>
#
# Two failure modes are handled, and only ONE of them is owned here:
#
#   1. CONTEXT FULL  — owned by ~/.claude/hooks/auto-compact-continue.sh
#      (Stop + PostCompact hooks, threshold via `--set`, default 70%). That
#      runs INSIDE the watched session and is the primary path. This script
#      only carries a BACKSTOP at $COMPACT_AT (default 85%) for when the Stop
#      hook never fires — e.g. the session is wedged mid-turn, so there is no
#      Stop event to hook. The backstop must also send the continue itself:
#      the PostCompact hook only continues a compaction IT started (it keys on
#      a pending marker holding the session_id, which we cannot forge).
#
#   2. MODEL LIMIT EXHAUSTED — owned here. Nothing else watches for it.
#      On detection: `/model opus`, then a continue prompt.
#
# SAFETY — everything is typed with `tmux send-keys`, so it can only ever go
# into an EMPTY input box; otherwise it gets appended to whatever the user is
# mid-way through typing and submitted with it. The box is read off-screen via
# cc-prompt-state (cc-notify plugin), exactly as auto-compact-continue.sh does.
# Unreadable box, or a pane whose title no longer matches, means we do NOTHING:
# a missed nudge is recoverable, a mangled message is not.
set -uo pipefail

SESS=${1:?usage: cc-watch-session.sh <tmux-session> [pane-title-substring]}
TITLE=${2:-}
INTERVAL=${INTERVAL:-600}          # 10 min
COMPACT_AT=${COMPACT_AT:-85}       # backstop only; the hook owns the normal path
COOLDOWN=${COOLDOWN:-1800}         # min seconds between actions of the same kind
CONTINUE_MSG=${CONTINUE_MSG:-'continue to achieve all your goals set by the user'}

TMP=${TMPDIR:-/tmp}
LOG=$TMP/cc-watch-$SESS.log
PIDFILE=$TMP/cc-watch-$SESS.pid

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" >>"$LOG"; }

# cc-prompt-state ships with the cc-notify plugin: dev checkout first, else the
# newest installed cache (version dirs change, so never hardcode one).
PROMPT_STATE=
for p in "$HOME/Projects/cc-notify/bin/cc-prompt-state" \
         $(ls -dt "$HOME"/.claude/plugins/cache/farishijazi-plugins/cc-notify/*/bin/cc-prompt-state 2>/dev/null); do
  [ -x "$p" ] && { PROMPT_STATE=$p; break; }
done

# Type $1 into the pane and submit it — but only into an empty input box.
send() {
  local want=$1 cur
  if [ -z "$PROMPT_STATE" ]; then
    log "ABORT no cc-prompt-state (cannot verify the input box is empty)"; return 1
  fi
  if ! "$PROMPT_STATE" "$SESS" >/dev/null 2>&1; then
    log "SKIP input box not empty / dialog open — will retry next tick"; return 1
  fi
  tmux send-keys -t "$SESS" -l -- "$want"
  sleep 0.2
  # The box can change in the gap between the check and now, so confirm it holds
  # exactly what we typed before pressing Enter. On a mismatch abort WITHOUT
  # backspacing: our text sits there unsent (visible, harmless), whereas blind
  # backspaces would eat characters someone just typed.
  cur=$("$PROMPT_STATE" "$SESS" 2>/dev/null)
  if [ "$cur" != "$want" ]; then
    log "ABORT before Enter — box is '$cur', expected '$want'"; return 1
  fi
  tmux send-keys -t "$SESS" Enter
  log "SENT '$want'"
}

# Seconds since the last action of kind $1 (huge number if never).
since() {
  local f=$TMP/cc-watch-$SESS.$1 t
  [ -r "$f" ] || { echo 999999; return; }
  t=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo 0)
  echo $(( $(date +%s) - t ))
}
stamp() { : >"$TMP/cc-watch-$SESS.$1"; }

# Singleton. Two daemons on one session means every action is sent TWICE — a
# double /compact, a double /model opus. The pidfile alone is not enough to
# prevent that (see release_pidfile), so the authority is a live process check.
existing=$(pgrep -f "cc-watch-session\.sh $SESS( |\$)" | grep -v "^$$\$" | head -1)
if [ -n "$existing" ]; then
  log "refusing to start: pid $existing is already watching '$SESS'"
  echo "already watching '$SESS' (pid $existing)" >&2
  exit 0
fi

# Only ever delete a pidfile we still own. A SIGTERM'd predecessor sits inside
# `sleep $INTERVAL` — bash defers the trap until that child returns — so it can
# wake up MINUTES after its replacement started and, with a blind `rm`, delete
# the successor's pidfile. That reads as DAEMON-DEAD to any supervisor, which
# then starts a duplicate. Observed 2026-08-16: two predecessors reaped ~9 min
# late, leaving a healthy daemon with no pidfile.
release_pidfile() {
  [ -r "$PIDFILE" ] && [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] && rm -f "$PIDFILE"
  return 0
}

echo $$ >"$PIDFILE"
log "watching '$SESS' (title~'$TITLE') every ${INTERVAL}s; compact backstop ${COMPACT_AT}%; pid $$"
trap 'log "stopping (pid $$)"; release_pidfile; exit 0' TERM INT

while :; do
  if ! tmux has-session -t "$SESS" 2>/dev/null; then
    log "session '$SESS' is gone — exiting"; release_pidfile; exit 0
  fi

  # Guard: sessions get renumbered/reused. Never type into the wrong agent.
  cur_title=$(tmux display-message -p -t "$SESS" '#{pane_title}' 2>/dev/null)
  case "$cur_title" in
    *"$TITLE"*) ;;
    *) log "SKIP pane title is '$cur_title', expected to contain '$TITLE'"
       sleep "$INTERVAL"; continue ;;
  esac

  visible=$(tmux capture-pane -t "$SESS" -p 2>/dev/null)

  # The statusline renders "<Model> <ver> ██████░░░░ NN%" — model name and
  # context-used percent in one place. A truncated statusline yields neither,
  # which correctly reads as "unknown" and makes us do nothing.
  #
  # ⚠️ The gap before the bar must be [^█░], NOT [0-9. ]: at ≥80% the statusline
  # inserts a 💀 warning glyph ("Fable 5 💀 ████████░░ 87%"). A digits-only class
  # parsed fine at 67/73/75% and then went blind at 87% — i.e. it failed exactly
  # at the threshold the backstop exists for, and silently, since an empty model
  # also defeats the limit detector's downgrade check.
  sline=$(printf '%s\n' "$visible" | grep -oE '(Fable|Opus|Sonnet|Haiku)[^█░]{0,20}[█░]{10} *[0-9]+%' | tail -1)
  model=$(printf '%s' "$sline" | grep -oE '^(Fable|Opus|Sonnet|Haiku)')
  pct=$(printf '%s' "$sline" | grep -oE '[0-9]+%$' | tr -d '%')

  # --- Signal 1: the model is no longer the one we started on. -------------
  # Structural, so it survives any rewording of the limit banner. Fable = still
  # running; Opus = we (or the user) already switched. Anything else is an
  # auto-downgrade, which is what exhausting the Fable allowance looks like.
  downgraded=0
  case "$model" in ''|Fable|Opus) ;; *) downgraded=1 ;; esac

  # --- Signal 2: an explicit limit banner on screen. -----------------------
  # Deliberately requires limit-wording AND a remedy word. The watched session
  # refactors a POWER controller whose source is full of "limit reached" style
  # text, so a bare /limit/ match would fire on its own code.
  banner=0
  printf '%s\n' "$visible" \
    | grep -qiE '((usage|model) limit|limit reached|limit will reset|out of (fable|opus|sonnet))' \
    && printf '%s\n' "$visible" | grep -qiE '(reset|upgrade|/model|switch|try again)' \
    && banner=1

  if { [ "$downgraded" = 1 ] || [ "$banner" = 1 ]; } && [ "$(since limit)" -gt "$COOLDOWN" ]; then
    log "LIMIT signal (model='$model' downgraded=$downgraded banner=$banner) → switching to opus"
    if send '/model opus'; then
      stamp limit
      sleep 2
      send "$CONTINUE_MSG"
    fi
    sleep "$INTERVAL"; continue
  fi

  # --- Context backstop (the Stop hook owns the normal 70% path). ----------
  # Only when the session is NOT mid-turn. cc-prompt-state reports an empty box
  # even while a turn is running, so without this the backstop would queue a
  # /compact into a live turn — and the Stop hook fires its OWN /compact the
  # moment that turn ends, giving two compactions racing each other. A working
  # session needs no backstop by definition: it will reach a Stop event.
  working=0
  printf '%s\n' "$visible" \
    | grep -qE '\([0-9]+m [0-9]+s ·|esc to interrupt|↓ *[0-9.]+k tokens' && working=1

  if [ "$working" = 0 ] && [ -n "$pct" ] && [ "$pct" -ge "$COMPACT_AT" ] && [ "$(since compact)" -gt "$COOLDOWN" ]; then
    log "context ${pct}% ≥ ${COMPACT_AT}% and the Stop hook has not compacted → backstop /compact"
    if send '/compact'; then
      stamp compact
      sleep 120                     # compaction is slow; the box is busy until it lands
      send "$CONTINUE_MSG"
    fi
    sleep "$INTERVAL"; continue
  fi

  log "ok — model=${model:-?} context=${pct:-?}%"
  sleep "$INTERVAL"
done
