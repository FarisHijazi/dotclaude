#!/usr/bin/env bash
# The X11 half of sudo.sh, exec'd by it on anything that is not macOS.
# Same contract and exit codes as sudo.sh; only the tab/key plumbing differs.
#
# Chrome extension shortcuts (Bitwarden's autofill) fire only on real X key
# events: keys sent through Claude in Chrome (CDP) never reach them, so this
# uses xdotool. X has no tab ids, so the target is found by its TITLE: each
# Chrome window is raised and Ctrl+Tab cycles its tabs until the window name
# starts with --title. Nothing is typed unless the front window shows it.
#
# usage: sudo-linux.sh <url> <title> <site> <via> <approve-label> <keys> <submit 0|1> <timeout>
set -euo pipefail

url=$1 title=$2 site=$3 via=$4 approve=$5 keys=$6 submit=$7 timeout=$8
[ -n "$title" ] || { echo "Linux needs --title <tab title prefix> (X has no tab ids)" >&2; exit 3; }
command -v xdotool >/dev/null || { echo "xdotool not installed (apt install xdotool)" >&2; exit 3; }
export DISPLAY=${DISPLAY:-:0} XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}
# Bitwarden's Linux binding is Ctrl, never Cmd: map the macOS default over.
keys=${keys//cmd/ctrl}

front_is_target() {
  case $(xdotool getactivewindow getwindowname 2>/dev/null) in "$title"*) return 0 ;; esac
  return 1
}

# select_tab: bring the tab whose title starts with $title to the front.
select_tab() {
  local w
  for w in $(xdotool search --onlyvisible --class google-chrome); do
    xdotool windowactivate --sync "$w" 2>/dev/null || continue
    for _ in $(seq 1 40); do
      front_is_target && return 0
      xdotool key --clearmodifiers ctrl+Tab
      sleep 0.15
    done
  done
  return 1
}

. "$(dirname "$0")/approve.sh"
request_approval "$site" "$approve" "$title" "$timeout" || exit 1
[ "$via" = password ] || { echo "approved: $via"; exit 0; }

select_tab || { echo "no Chrome tab titled '$title' on $DISPLAY: $url" >&2; exit 2; }
sleep 1 # let the page take key focus after the switch
front_is_target || { echo "front window is not '$title'; sent nothing" >&2; exit 4; }
xdotool key --clearmodifiers "$keys"
if [ "$submit" = 1 ]; then
  sleep 0.8
  front_is_target || { echo "focus moved after the fill; did not submit" >&2; exit 4; }
  xdotool key --clearmodifiers Return
  echo "filled and submitted: $title"
else
  echo "filled: $title"
fi
