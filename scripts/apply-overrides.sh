#!/usr/bin/env bash
# Manage .claude.json overrides: extract current values or apply them to a new machine.
#   apply-overrides.sh extract  — pull current values from ~/.claude.json into overrides file
#   apply-overrides.sh apply    — deep-merge overrides into ~/.claude.json
set -euo pipefail

BASE=~/.claude.json
OVER=~/.claude/.claude.json.overrides.json

case "${1:-apply}" in
  extract)
    # Read keys already in overrides, refresh their values from the live .claude.json
    keys=$(jq -r 'keys[]' "$OVER")
    filter=$(printf '{%s}' "$(echo "$keys" | while read -r k; do printf '"%s": ."%s",' "$k" "$k"; done)")
    jq "$filter" "$BASE" > "$OVER"
    echo "Extracted → $OVER"
    ;;
  apply)
    tmp=$(mktemp)
    jq -s '.[0] * .[1]' "$BASE" "$OVER" > "$tmp" && mv "$tmp" "$BASE"
    echo "Applied overrides → $BASE"
    ;;
  *)
    echo "Usage: $0 [extract|apply]" >&2; exit 1
    ;;
esac
