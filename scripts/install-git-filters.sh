#!/usr/bin/env bash
# One-time per machine: teach this clone the settings.json filter.
# A repository cannot configure its own filters (that would let a clone run code
# on checkout), so this has to be run by hand once — see scripts/settings-filter.sh.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

command -v jq >/dev/null 2>&1 || { echo "jq is required" >&2; exit 1; }

git config filter.claude-settings.clean  "bash scripts/settings-filter.sh clean"
git config filter.claude-settings.smudge "bash scripts/settings-filter.sh smudge"

# Snapshot what this machine currently has, so the first checkout can restore it.
bash scripts/settings-filter.sh save

# git only re-runs a filter when it thinks the file changed, so an already-tracked
# settings.json keeps its old (key-carrying) blob until it is renormalized.
git add --renormalize settings.json

echo "filter installed. settings.json's enabledPlugins now stays out of git;"
echo "this machine's copy lives in the untracked settings.plugins.local.json."
