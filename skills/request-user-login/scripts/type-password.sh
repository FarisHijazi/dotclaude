#!/usr/bin/env bash
# type-password: answer a terminal password prompt (sudo, ssh, su, gpg...)
# sitting in a tmux pane, after the user approves through approve.sh.
# The secret goes keychain/vault -> tmux paste buffer -> pane. It never hits
# stdout, a file or argv (send-keys -l "$pw" would show it in `ps`), so the
# caller (Claude) never sees it.
#
# usage: type-password.sh <tmux-pane> <name> [--from keychain|bw] [--for <grant>] [--timeout 120]
#   <name>  keychain: the account of a generic password with service
#           "request-user-login" (user adds it once with
#           `security add-generic-password -s request-user-login -a <name> -w`)
#           bw: a Bitwarden item name or id (needs an unlocked `bw`, BW_SESSION set)
# exit:  0 typed, prompt accepted | 1 declined | 2 no password prompt in the pane
#        3 usage | 5 typed but rejected ("Sorry, try again", "Permission denied")
#        6 secret not found
set -euo pipefail

pane="" name="" from=keychain grant="" timeout=120
while [ $# -gt 0 ]; do
  case $1 in
    --from) from=$2; shift 2 ;;
    --for) grant=$2; shift 2 ;;
    --timeout) timeout=$2; shift 2 ;;
    -*) echo "unknown flag: $1" >&2; exit 3 ;;
    *) if [ -z "$pane" ]; then pane=$1; else name=$1; fi; shift ;;
  esac
done
[ -n "$pane" ] && [ -n "$name" ] || { sed -n 2,16p "$0" >&2; exit 3; }
[ -n "$grant" ] || grant="password-$name"

prompt_re='(password|passphrase|passcode)[^:]*: *$'
last_line() { tmux capture-pane -p -t "$pane" | grep -v '^[[:space:]]*$' | tail -1; }

# Only ever type into a waiting password prompt, never into a shell or editor.
# Give a just-started sudo/ssh up to 20 s to show it.
for _ in $(seq 40); do
  last_line | grep -qiE "$prompt_re" && break
  sleep 0.5
done
line=$(last_line)
grep -qiE "$prompt_re" <<<"$line" || { echo "no password prompt in $pane (last line: $line)" >&2; exit 2; }
cmd=$(tmux display -p -t "$pane" '#{pane_current_command}')

. "$(dirname "$0")/approve.sh"
request_approval "$grant" "Type password ($name)" "$cmd: $line" "$timeout" || exit 1

buf="rul-$$"
trap 'tmux delete-buffer -b "$buf" 2>/dev/null || true' EXIT
case $from in
  keychain) security find-generic-password -s request-user-login -a "$name" -w 2>/dev/null ;;
  bw) bw get password "$name" 2>/dev/null ;;
  *) echo "unknown --from: $from" >&2; exit 3 ;;
esac | tr -d '\n' | tmux load-buffer -b "$buf" - || true
[ -n "$(tmux show-buffer -b "$buf" 2>/dev/null | head -c1)" ] || { echo "no secret for $name in $from" >&2; exit 6; }

# Re-check right before typing: the prompt must still be there.
grep -qiE "$prompt_re" <<<"$(last_line)" || { echo "prompt went away; typed nothing" >&2; exit 2; }
tmux paste-buffer -d -b "$buf" -t "$pane"
tmux send-keys -t "$pane" Enter

sleep 2
if tmux capture-pane -p -t "$pane" | grep -v '^[[:space:]]*$' | tail -3 | grep -qiE 'sorry, try again|permission denied|incorrect password|authentication fail'; then
  echo "password rejected in $pane" >&2; exit 5
fi
echo "typed password for $name into $pane"
