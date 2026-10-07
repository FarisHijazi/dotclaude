#!/usr/bin/env bash
# confirm-passkey: when a site has opened Bitwarden's "Log in with passkey?"
# window, ask the user with a FRESH notification click (never a reused grant:
# this is the second factor, so it gets its own approval every time), then
# press the passkey entry whose text contains <match> (e.g. the site's
# domain). Works only for Bitwarden passkeys; a Touch ID prompt needs a finger.
#
# usage: confirm-passkey.sh <match> [--timeout 120]
# exit:  0 pressed | 1 declined / timed out | 2 Bitwarden window or entry not found | 3 usage
set -euo pipefail
dir=$(cd "$(dirname "$0")" && pwd)  # absolute: hs resolves dofile paths from its own cwd
match="" timeout=120
while [ $# -gt 0 ]; do
  case $1 in
    --timeout) timeout=$2; shift 2 ;;
    -*) echo "unknown flag: $1" >&2; exit 3 ;;
    *) match=$1; shift ;;
  esac
done
[ -n "$match" ] || { sed -n 2,10p "$0" >&2; exit 3; }

. "$dir/approve.sh"
GRANT_SECONDS=0  # second factor: always ask, never reuse an earlier click
request_approval "passkey:$match" "Use passkey" "Bitwarden passkey for $match" "$timeout" || exit 1

# Lua strings: escape backslashes and quotes in the match text.
m=${match//\\/\\\\}; m=${m//\"/\\\"}
# -t 30: the tree walk takes longer than hs's 4 s default IPC timeout.
out=$(/opt/homebrew/bin/hs -t 30 -c "PASSKEY_MATCH = \"$m\"; return dofile(\"$dir/press_passkey.lua\")" </dev/null | tail -1)
echo "$out"
[ "$out" = pressed ] || exit 2
