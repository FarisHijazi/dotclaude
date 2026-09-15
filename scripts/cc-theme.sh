#!/usr/bin/env bash
# Set a RUNNING Claude Code session's theme.
#
# Why this is not just a settings.json write: a live session does not re-read
# the `theme` key (verified -- flipping it mid-session left the rendered palette
# byte-identical). Editing settings.json only takes effect for the NEXT session.
# The one lever a running session exposes is the /theme popup.
#
# Why it does not count arrow presses: the popup opens with the cursor on the
# CURRENT theme, so any fixed number of Up/Down is wrong from every other
# starting point -- and the list grows once you save a custom theme. But the
# menu is NUMBERED and a digit selects directly, so this reads the menu off the
# pane, finds the line whose label matches, and presses that digit. Starting
# position stops mattering.
#
#   cc-theme.sh <name> [tmux-target]      target defaults to the current pane
#   cc-theme.sh --list [tmux-target]      show the menu and which one is active
#
#   names: auto dark light dark-daltonized light-daltonized dark-ansi light-ansi
#
# Typing into a TUI follows the same rules as cc-color-apply.sh: only into an
# empty input box, hold the pane type-lock so the /color and /compact hooks
# cannot interleave, and verify against the pane rather than trusting a single
# read (a recognised slash command is coloured, and an open menu hides the box).
set -uo pipefail

MARK=$'\342\235\257'
NBSP=$'\302\240'

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

label_for() {  # theme name -> the exact menu label, anchored so "Dark mode"
  case "$1" in                      # cannot match "Dark mode (ANSI colors only)"
    auto)             printf 'Auto (match terminal)' ;;
    dark)             printf 'Dark mode' ;;
    light)            printf 'Light mode' ;;
    dark-daltonized)  printf 'Dark mode (colorblind-friendly)' ;;
    light-daltonized) printf 'Light mode (colorblind-friendly)' ;;
    dark-ansi)        printf 'Dark mode (ANSI colors only)' ;;
    light-ansi)       printf 'Light mode (ANSI colors only)' ;;
    *) return 1 ;;
  esac
}

# cc-prompt-state ships with cc-notify; dev checkout first, else newest cached.
find_prompt_state() {
  local best='' f
  shopt -s nullglob
  for f in "$HOME"/Projects/cc-notify/bin/cc-prompt-state \
           "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/cache/*/cc-notify/*/bin/cc-prompt-state; do
    [[ -x "$f" && ( -z "$best" || "$f" -nt "$best" ) ]] && best="$f"
  done
  shopt -u nullglob
  printf '%s' "$best"
}

arg1="${1:-}"; [[ -z "$arg1" || "$arg1" == -h || "$arg1" == --help ]] && usage 0
if [[ "$arg1" == --list ]]; then target="${2:-}"; else target="${2:-}"; fi
[[ -n "$target" ]] || target=$(tmux display-message -p '#S:#I.#P' 2>/dev/null) || {
  echo "no tmux target given and not inside tmux" >&2; exit 2; }

prompt_state=$(find_prompt_state)
[[ -x "$prompt_state" ]] || { echo "cc-prompt-state not found (cc-notify)" >&2; exit 2; }
lock_lib="$(dirname "$prompt_state")/cc-type-lock.sh"
# shellcheck source=/dev/null
[[ -r "$lock_lib" ]] && . "$lock_lib"
declare -F cc_type_lock >/dev/null || { cc_type_lock() { :; }; cc_type_unlock() { :; }; }

menu_open() { tmux capture-pane -p -t "$target" | grep -q 'Choose the text style'; }
still_typed() {
  tmux capture-pane -p -t "$target" 2>/dev/null | tail -12 | grep -qF -- "$MARK$NBSP${1:0:24}"
}

# Print the menu as "<digit><TAB><label><TAB><active?>".
read_menu() {
  tmux capture-pane -p -t "$target" |
    sed -n 's/^\( *'"$MARK"'\)\{0,1\} *\([0-9]\{1,2\}\)\. \(.*\)$/\2\t\3/p' |
    while IFS=$'\t' read -r n rest; do
      local act=''; case "$rest" in *✔*) act='active' ;; esac
      rest="${rest%%✔*}"; rest="${rest%"${rest##*[![:space:]]}"}"
      printf '%s\t%s\t%s\n' "$n" "$rest" "$act"
    done
}

open_menu() {
  local want='/theme'
  cc_type_lock "$target" || { echo "another hook holds the pane type-lock" >&2; return 1; }
  if ! "$prompt_state" "$target" >/dev/null 2>&1; then
    cc_type_unlock; echo "input box not empty (or no box) — refusing to type" >&2; return 1
  fi
  tmux send-keys -t "$target" -l -- "$want"
  sleep "${CC_THEME_ENTER_DELAY:-1}"
  still_typed "$want" || { cc_type_unlock; echo "'$want' never reached the input row" >&2; return 1; }
  tmux send-keys -t "$target" Enter
  local i
  for ((i = 0; i < 20; i++)); do menu_open && return 0; sleep 0.25; done
  cc_type_unlock; echo "theme menu did not open" >&2; return 1
}

if [[ "$arg1" == --list ]]; then
  open_menu || exit 1
  read_menu | while IFS=$'\t' read -r n l a; do printf '  %s. %-34s %s\n' "$n" "$l" "$a"; done
  tmux send-keys -t "$target" Escape; cc_type_unlock; exit 0
fi

want_label=$(label_for "$arg1") || { echo "unknown theme: $arg1" >&2; usage 2; }
open_menu || exit 1

digit=$(read_menu | awk -F'\t' -v L="$want_label" '$2 == L { print $1; exit }')
if [[ -z "$digit" ]]; then
  tmux send-keys -t "$target" Escape; cc_type_unlock
  echo "no menu entry labelled '$want_label'" >&2; exit 1
fi
tmux send-keys -t "$target" -l -- "$digit"

for ((i = 0; i < 20; i++)); do menu_open || break; sleep 0.25; done
cc_type_unlock
if menu_open; then echo "menu still open after pressing $digit" >&2; exit 1; fi
echo "theme set to $arg1 (menu item $digit) in $target"
