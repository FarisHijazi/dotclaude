#!/usr/bin/env bash
# Materialise the plugins that settings.json declares.
#
# settings.json (tracked) is the declaration; ~/.claude/plugins/*.json
# (untracked, absolute paths, sometimes a PAT) is the materialisation.
# Cloning this repo brings the first and not the second, which is what
# "cache miss" means. This script closes that gap, and is idempotent, so
# it doubles as the repair tool.  See docs/plugins-mcp-and-connectors.md
#
#   install-plugins.sh                 # install what is missing
#   install-plugins.sh --dry-run       # print the plan only
#   install-plugins.sh --prune-missing # also drop dead registry records
set -uo pipefail

SETTINGS="${CLAUDE_SETTINGS_FILE:-$HOME/.claude/settings.json}"
PLUGDIR="${CLAUDE_PLUGIN_DIR:-$HOME/.claude/plugins}"
CLAUDE="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
DRY=0; PRUNE=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --prune-missing) PRUNE=1 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

[ -s "$SETTINGS" ] || { echo "no settings at $SETTINGS" >&2; exit 1; }
[ -x "$CLAUDE" ]   || { echo "no claude binary ($CLAUDE)" >&2; exit 1; }

run() {  # echo, then execute unless --dry-run
  printf '  $ %s\n' "$*"
  [ "$DRY" = 1 ] || "$@"
}

# --- marketplaces ------------------------------------------------------
# A declared name is missing when known_marketplaces.json has no such key.
have_mkt() { jq -e --arg n "$1" 'has($n)' "$PLUGDIR/known_marketplaces.json" >/dev/null 2>&1; }

echo "== marketplaces"
while IFS=$'\t' read -r name src; do
  [ -n "$name" ] || continue
  if have_mkt "$name"; then echo "  ok      $name"; continue; fi
  echo "  MISSING $name"
  run "$CLAUDE" plugin marketplace add "$src"
done < <(jq -r '
  (.extraKnownMarketplaces // {}) | to_entries[]
  | [ .key, (.value.source.repo // .value.source.url // .value.source.path // empty) ]
  | @tsv' "$SETTINGS")

# --- plugins -----------------------------------------------------------
# Declared-and-true but absent from installed_plugins.json. That registry,
# not the cache directory, is what `claude plugin list` reads.
have_plugin() { jq -e --arg p "$1" '.plugins | has($p)' "$PLUGDIR/installed_plugins.json" >/dev/null 2>&1; }

echo "== plugins"
while read -r id; do
  [ -n "$id" ] || continue
  if have_plugin "$id"; then echo "  ok      $id"; continue; fi
  echo "  MISSING $id"
  run "$CLAUDE" plugin install "$id" -y
done < <(jq -r '(.enabledPlugins // {}) | to_entries[] | select(.value == true) | .key' "$SETTINGS")

# --- the real cache miss ----------------------------------------------
# A registry record whose installPath is gone from disk. This is what Claude
# Code reports as `plugin-cache-miss`, and unlike a missing registry record it
# never self-heals. Reinstall if the plugin is still declared; otherwise the
# record is dead and only --prune-missing removes it.
echo "== registry records whose payload is missing on disk"
REG="$PLUGDIR/installed_plugins.json"
if [ -s "$REG" ]; then
  while IFS=$'\t' read -r id path; do
    [ -n "$id" ] && [ -n "$path" ] || continue
    [ -d "$path" ] && continue
    declared=$(jq -r --arg p "$id" '(.enabledPlugins // {})[$p] // "absent"' "$SETTINGS")
    echo "  MISS    $id  ($path)"
    if [ "$declared" = "true" ]; then
      run "$CLAUDE" plugin install "$id" -y
    elif [ "$PRUNE" = 1 ]; then
      echo "    not declared -> dropping dead record"
      if [ "$DRY" != 1 ]; then
        tmp=$(mktemp) && jq --arg p "$id" 'del(.plugins[$p])' "$REG" > "$tmp" && mv "$tmp" "$REG"
      fi
    else
      echo "    not declared -> stale; re-run with --prune-missing to drop it"
    fi
  done < <(jq -r '.plugins // {} | to_entries[] | .key as $k | .value[] | [$k, .installPath] | @tsv' "$REG")
fi

# --- the other direction ----------------------------------------------
# Installed but not declared: fine on a machine with private marketplaces
# (settings-filter.sh privatize), noise otherwise. Never auto-removed.
echo "== installed but not declared (informational)"
comm -13 \
  <(jq -r '(.enabledPlugins // {}) | keys[]' "$SETTINGS" | sort) \
  <(jq -r '.plugins | keys[]' "$PLUGDIR/installed_plugins.json" 2>/dev/null | sort) \
  | sed 's/^/  extra   /'
exit 0
