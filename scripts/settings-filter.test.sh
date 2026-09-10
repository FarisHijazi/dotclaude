#!/usr/bin/env bash
# Exercise settings-filter.sh against throwaway files in a temp dir.
# Touches no real settings: both paths are overridden by env var.
# Run: bash scripts/settings-filter.test.sh
set -uo pipefail
F="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/settings-filter.sh"
d=$(mktemp -d)
export CLAUDE_SETTINGS_FILE="$d/settings.json"
export CLAUDE_SETTINGS_LOCAL="$d/local.json"
pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; echo "        want: $3"; echo "        got:  $2"; fail=$((fail+1)); fi; }

cat > "$CLAUDE_SETTINGS_FILE" <<'J'
{
  "model": "opus",
  "enabledPlugins": {"a@shared1": true, "b@priv1": false},
  "extraKnownMarketplaces": {
    "shared1": {"source": {"source": "github", "repo": "o/shared1"}},
    "shared2": {"source": {"source": "github", "repo": "o/shared2"}},
    "priv1":   {"source": {"source": "github", "repo": "o/priv1"}}
  }
}
J
orig=$(cat "$CLAUDE_SETTINGS_FILE")

# 1. save with no local file: plugins only, no marketplaces promoted
bash "$F" save >/dev/null
ck "save snapshots enabledPlugins"      "$(jq -c '.enabledPlugins|keys' "$CLAUDE_SETTINGS_LOCAL")" '["a@shared1","b@priv1"]'
ck "save promotes no marketplace"       "$(jq -c 'has("extraKnownMarketplaces")' "$CLAUDE_SETTINGS_LOCAL")" 'false'

# 2. clean before privatize: strips plugins, keeps every marketplace
c1=$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE")
ck "clean drops enabledPlugins"         "$(echo "$c1" | jq -c 'has("enabledPlugins")')" 'false'
ck "clean keeps all marketplaces"       "$(echo "$c1" | jq -c '.extraKnownMarketplaces|keys')" '["priv1","shared1","shared2"]'
ck "clean keeps unrelated keys"         "$(echo "$c1" | jq -r '.model')" 'opus'

# 3. privatize
bash "$F" privatize priv1 >/dev/null
ck "privatize records the name"         "$(jq -c '.extraKnownMarketplaces|keys' "$CLAUDE_SETTINGS_LOCAL")" '["priv1"]'
ck "privatize copies the value"         "$(jq -r '.extraKnownMarketplaces.priv1.source.repo' "$CLAUDE_SETTINGS_LOCAL")" 'o/priv1'

# 4. clean after privatize
c2=$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE")
ck "clean strips the private one"       "$(echo "$c2" | jq -c '.extraKnownMarketplaces|keys')" '["shared1","shared2"]'

# 5. smudge restores everything -> byte-equal round trip
s=$(echo "$c2" | bash "$F" smudge)
ck "smudge restores plugins"            "$(echo "$s" | jq -c '.enabledPlugins|keys')" '["a@shared1","b@priv1"]'
ck "smudge restores the private one"    "$(echo "$s" | jq -c '.extraKnownMarketplaces|keys')" '["priv1","shared1","shared2"]'
ck "round trip equals the original"     "$(echo "$s" | jq -S -c .)" "$(echo "$orig" | jq -S -c .)"

# 6. clean is idempotent through a round trip
ck "clean(smudge(clean)) == clean"      "$(echo "$s" | bash "$F" clean | jq -S -c .)" "$(echo "$c2" | jq -S -c .)"

# 7. save keeps the private marketplace and refreshes its value
jq '.extraKnownMarketplaces.priv1.source.repo = "o/priv1-moved"' "$CLAUDE_SETTINGS_FILE" > "$d/t" && mv "$d/t" "$CLAUDE_SETTINGS_FILE"
bash "$F" save >/dev/null
ck "save refreshes a private value"     "$(jq -r '.extraKnownMarketplaces.priv1.source.repo' "$CLAUDE_SETTINGS_LOCAL")" 'o/priv1-moved'
ck "save still promotes nothing new"    "$(jq -c '.extraKnownMarketplaces|keys' "$CLAUDE_SETTINGS_LOCAL")" '["priv1"]'

# 8. a session prunes the private marketplace out of settings.json -> save must keep it
jq 'del(.extraKnownMarketplaces.priv1)' "$CLAUDE_SETTINGS_FILE" > "$d/t" && mv "$d/t" "$CLAUDE_SETTINGS_FILE"
bash "$F" save >/dev/null
ck "save survives a pruning session"    "$(jq -r '.extraKnownMarketplaces.priv1.source.repo' "$CLAUDE_SETTINGS_LOCAL")" 'o/priv1-moved'

# 9. the empty-snapshot guard still holds
jq 'del(.enabledPlugins)' "$CLAUDE_SETTINGS_FILE" > "$d/t" && mv "$d/t" "$CLAUDE_SETTINGS_FILE"
bash "$F" save >/dev/null
ck "save refuses to wipe a snapshot"    "$(jq -c '.enabledPlugins|keys' "$CLAUDE_SETTINGS_LOCAL")" '["a@shared1","b@priv1"]'

# 10. restore puts both keys back
bash "$F" restore >/dev/null
ck "restore returns enabledPlugins"     "$(jq -c '.enabledPlugins|keys' "$CLAUDE_SETTINGS_FILE")" '["a@shared1","b@priv1"]'
ck "restore returns the private one"    "$(jq -r '.extraKnownMarketplaces.priv1.source.repo' "$CLAUDE_SETTINGS_FILE")" 'o/priv1-moved'

# 11. share undoes it
bash "$F" share priv1 >/dev/null
ck "share drops it from the snapshot"   "$(jq -c '.extraKnownMarketplaces|keys' "$CLAUDE_SETTINGS_LOCAL")" '[]'
ck "clean then keeps it again"          "$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE" | jq -c '.extraKnownMarketplaces|keys')" '["priv1","shared1","shared2"]'

# 12. no local file at all: clean/smudge must still behave
rm -f "$CLAUDE_SETTINGS_LOCAL"
ck "clean with no snapshot"             "$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE" | jq -c 'has("enabledPlugins")')" 'false'
ck "smudge with no snapshot is a passthrough" "$(bash "$F" smudge < "$CLAUDE_SETTINGS_FILE" | jq -S -c .)" "$(jq -S -c . "$CLAUDE_SETTINGS_FILE")"

# 13. a name can be marked private BEFORE the marketplace exists here
rm -f "$CLAUDE_SETTINGS_LOCAL"
bash "$F" save >/dev/null
bash "$F" privatize notyet >/dev/null
ck "privatize records an absent name"   "$(jq -c '.privateMarketplaces' "$CLAUDE_SETTINGS_LOCAL")" '["notyet"]'
ck "no empty value is cached"           "$(jq -c 'has("extraKnownMarketplaces")' "$CLAUDE_SETTINGS_LOCAL")" 'false'
sm=$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE" | bash "$F" smudge)
ck "smudge injects no empty entry"      "$(echo "$sm" | jq -c '.extraKnownMarketplaces|keys')" '["priv1","shared1","shared2"]'
ck "smudge never leaks the name list"   "$(echo "$sm" | jq -c 'has("privateMarketplaces")')" 'false'

# 14. once it IS installed, clean strips it and smudge brings it back
jq '.extraKnownMarketplaces.notyet = {"source":{"repo":"o/notyet"}}' "$CLAUDE_SETTINGS_FILE" > "$d/t" && mv "$d/t" "$CLAUDE_SETTINGS_FILE"
bash "$F" save >/dev/null
ck "save now caches its value"          "$(jq -r '.extraKnownMarketplaces.notyet.source.repo' "$CLAUDE_SETTINGS_LOCAL")" 'o/notyet'
c3=$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE")
ck "clean strips the newly-installed"   "$(echo "$c3" | jq -c '.extraKnownMarketplaces|keys')" '["priv1","shared1","shared2"]'
ck "smudge restores it"                 "$(echo "$c3" | bash "$F" smudge | jq -c '.extraKnownMarketplaces|keys')" '["notyet","priv1","shared1","shared2"]'
ck "full round trip is byte-equal"      "$(echo "$c3" | bash "$F" smudge | jq -S -c .)" "$(jq -S -c . "$CLAUDE_SETTINGS_FILE")"

# 15. share clears the name from the list as well as the cache
bash "$F" share notyet >/dev/null
ck "share empties the name list"        "$(jq -c '.privateMarketplaces' "$CLAUDE_SETTINGS_LOCAL")" '[]'
ck "clean keeps it again"               "$(bash "$F" clean < "$CLAUDE_SETTINGS_FILE" | jq -c '.extraKnownMarketplaces|keys')" '["notyet","priv1","shared1","shared2"]'

rm -rf "$d"
echo "  ---- $pass passed, $fail failed"
exit $((fail > 0))
