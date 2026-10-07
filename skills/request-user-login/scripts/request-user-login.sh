#!/usr/bin/env bash
# request-user-login: ask the user, via a macOS notification, to approve a
# Bitwarden autofill in the Chrome tab whose URL starts with <url-prefix>.
# Only if they click the notification: select that tab, focus its window,
# send Bitwarden's autofill shortcut through Hammerspoon, then Return to submit.
# The password goes Bitwarden -> page; the caller never sees it.
#
# With --via google|passkey it only asks; on approval it exits 0 and the caller
# (Claude in Chrome) clicks the SSO / passkey buttons itself.
#
# One approval covers the whole login to --for <site> (default: the URL's host)
# for 5 minutes, so later steps of that login (e.g. a password step on
# accounts.google.com while logging in to chat.example.com) don't ask again.
#
# usage: request-user-login.sh <url-prefix> [--tab-id <claude-in-chrome tabId>] [--for <site>] [--via password|google|passkey]
#          [--keys cmd+shift+l] [--no-submit] [--timeout 120]
# exit:  0 filled (and submitted), or approved for --via google|passkey | 1 declined / timed out | 2 tab not found | 3 usage
#        4 target tab not in front at send time (nothing typed)
set -euo pipefail

url="" tab_id="" site="" via=password keys="cmd+shift+l" submit=1 timeout=120
while [ $# -gt 0 ]; do
  case $1 in
    --for) site=$2; shift 2 ;;
    --tab-id) tab_id=$2; shift 2 ;;
    --via) via=$2; shift 2 ;;
    --keys) keys=$2; shift 2 ;;
    --no-submit) submit=0; shift ;;
    --timeout) timeout=$2; shift 2 ;;
    -*) echo "unknown flag: $1" >&2; exit 3 ;;
    *) url=$1; shift ;;
  esac
done
[ -n "$url" ] || { sed -n 2,18p "$0" >&2; exit 3; }
[ -n "$site" ] || { site=${url#*://}; site=${site%%/*}; }

case $via in
  password) approve="Fill & sign in" ;;
  google) approve="Sign in with Google" ;;
  passkey) approve="Use passkey" ;;
  *) echo "unknown --via: $via" >&2; exit 3 ;;
esac

# chrome_tab find|select: print the title (or URL, if the title is empty) of
# the target tab, or nothing if there is none. The target is --tab-id when
# given (Claude in Chrome's tabId equals AppleScript's tab id), else the first
# tab whose URL starts with $url. "select" also activates it and raises its window.
chrome_tab() {
  osascript - "$url" "$1" "$tab_id" <<'EOF'
on run argv
  set {target, wanted, tabId} to argv
  tell application "Google Chrome"
    repeat with w in windows
      repeat with i from 1 to (count tabs of w)
        try -- tabs can close mid-scan; skip ones that vanish
          set t to tab i of w
          if tabId is "" then
            set hit to (URL of t) starts with target
          else
            set hit to ((id of t) as text) is tabId
          end if
          if hit then
            -- read before "set index": it renumbers windows, so w
            -- (window N of every window) points elsewhere afterwards
            set tabLabel to title of t
            if tabLabel is "" then set tabLabel to URL of t
            if wanted is "select" then
              set active tab index of w to i
              set index of w to 1
              activate
            end if
            return tabLabel
          end if
        end try
      end repeat
    end repeat
  end tell
  return ""
end run
EOF
}
title=$(chrome_tab find)
[ -n "$title" ] || { echo "no Chrome tab matching ${tab_id:-$url}" >&2; exit 2; }

. "$(dirname "$0")/approve.sh"
request_approval "$site" "$approve" "$title" "$timeout" || exit 1
[ "$via" = password ] || { echo "approved: $via"; exit 0; }

title=$(chrome_tab select)
[ -n "$title" ] || { echo "tab closed before approval: $url" >&2; exit 2; }

# AeroSpace keeps windows on other workspaces hidden; focusing by id switches to it.
if command -v aerospace >/dev/null; then
  wid=$(aerospace list-windows --all --format '%{window-id}|%{app-name}|%{window-title}' |
    awk -F'|' -v t="$title - " '$2=="Google Chrome" && index($3, t)==1 {print $1; exit}')
  [ -n "$wid" ] && aerospace focus --window-id "$wid"
fi
sleep 1  # let the window/workspace switch settle so the page has key focus
# Refuse to type anywhere else: the front window's active tab must be the target.
front=$(osascript -e 'tell application "Google Chrome" to return (id of active tab of front window as text) & " " & URL of active tab of front window')
if [ -n "$tab_id" ]; then ok=$([ "${front%% *}" = "$tab_id" ] && echo y)
else case ${front#* } in "$url"*) ok=y ;; esac; fi
[ "${ok:-}" = y ] || { echo "front tab is ${front#* }, not the target; sent nothing" >&2; exit 4; }

# Hammerspoon posts the keys under its own Accessibility grant (hs.ipc, no TCC
# prompt for the caller). Each modifier gets its own down/up event like a real
# keyboard: hs.eventtap.keyStroke only sets flags on the letter, which Chrome
# does not route to extension shortcuts. "cmd+shift+b" -> {"cmd","shift"}, "b".
key=${keys##*+} mods=""
if [ "$key" != "$keys" ]; then mods=\"${keys%+*}\"; mods=${mods//+/\",\"}; fi
sent=$(/opt/homebrew/bin/hs -c "
local E, mods, key = hs.eventtap.event, {$mods}, '$key'
if hs.application.frontmostApplication():bundleID() ~= 'com.google.Chrome' then return 'chrome not frontmost' end
local function post(e) e:post(); hs.timer.usleep(30000) end
for _, m in ipairs(mods) do post(E.newKeyEvent(m, true)) end
post(E.newKeyEvent(mods, key, true)); post(E.newKeyEvent(mods, key, false))
for i = #mods, 1, -1 do post(E.newKeyEvent(mods[i], false)) end
return 'sent'" </dev/null | tail -1)
# hs -c also prints module-loading chatter, so check the last line only.
[ "$sent" = sent ] || { echo "$sent; sent nothing" >&2; exit 4; }
if [ "$submit" = 1 ]; then
  sleep 0.8
  /opt/homebrew/bin/hs -c "hs.eventtap.keyStroke({}, 'return')" </dev/null >/dev/null
  echo "filled and submitted: $title"
else
  echo "filled: $title"
fi
