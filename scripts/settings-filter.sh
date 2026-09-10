#!/usr/bin/env bash
# Keep machine-local keys of settings.json out of git, without untracking the file.
#
# `enabledPlugins` is per-machine state (which plugins this box has installed and
# switched on) living inside a file that is otherwise shared. There is no
# user-level settings.local.json — Claude Code only reads ~/.claude/settings.json
# at the user scope (project-local overrides exist, user-local ones do not) — so
# the key cannot simply be moved somewhere untracked.
#
# A git filter is the mechanism for exactly this:
#   clean  (worktree -> index)  strips the key, so the repo copy never has it
#   smudge (index -> worktree)  puts THIS machine's value back from a local file
#
# Filters are per-clone by design (a repo cannot configure its own), so run
# scripts/install-git-filters.sh once on each machine. See also
# scripts/apply-overrides.sh, which solves the mirror-image problem for the
# untracked ~/.claude.json.
#
#   settings-filter.sh clean | smudge     (git calls these; stdin -> stdout)
#   settings-filter.sh save               snapshot the live key into the local file
#   settings-filter.sh show               print what the local file holds
set -euo pipefail

LOCAL="${CLAUDE_SETTINGS_LOCAL:-$HOME/.claude/settings.plugins.local.json}"
KEY=enabledPlugins

command -v jq >/dev/null 2>&1 || { cat; exit 0; }   # no jq: pass through untouched

case "${1:-}" in
  clean)
    jq --arg k "$KEY" 'del(.[$k])'
    ;;
  smudge)
    if [ -s "$LOCAL" ]; then
      # `*` deep-merges; the local file wins for the key it carries.
      jq -s '.[0] * .[1]' - "$LOCAL"
    else
      cat
    fi
    ;;
  save)
    jq --arg k "$KEY" '{($k): (.[$k] // {})}' "$HOME/.claude/settings.json" > "$LOCAL"
    echo "saved $KEY ($(jq --arg k "$KEY" '.[$k] | length' "$LOCAL") entries) -> $LOCAL"
    ;;
  show)
    [ -s "$LOCAL" ] && cat "$LOCAL" || echo "no $LOCAL yet — run: $0 save"
    ;;
  *)
    echo "usage: $0 clean|smudge|save|show" >&2; exit 1
    ;;
esac
