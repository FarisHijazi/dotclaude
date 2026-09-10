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
#   settings-filter.sh restore            merge the local file back into settings.json
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
    # NEVER clobber a good snapshot with an empty one. On a machine that has just
    # pulled, settings.json has no enabledPlugins yet (the filter was not
    # installed when git wrote it) — saving then would wipe the very thing we are
    # about to restore.
    live=$(jq --arg k "$KEY" '.[$k] | length' "$HOME/.claude/settings.json")
    if [ "$live" -eq 0 ] && [ -s "$LOCAL" ]; then
      echo "settings.json has no $KEY; keeping the existing $LOCAL ($(jq --arg k "$KEY" '.[$k] | length' "$LOCAL") entries)"
      exit 0
    fi
    jq --arg k "$KEY" '{($k): (.[$k] // {})}' "$HOME/.claude/settings.json" > "$LOCAL"
    echo "saved $KEY ($live entries) -> $LOCAL"
    ;;
  restore)
    # Put the key back into a settings.json that a checkout wrote without it.
    # Merges rather than checking the file out, so unrelated local edits survive.
    [ -s "$LOCAL" ] || { echo "no $LOCAL to restore from"; exit 0; }
    if [ "$(jq --arg k "$KEY" '.[$k] | length' "$HOME/.claude/settings.json")" -gt 0 ]; then
      echo "settings.json already has $KEY; nothing to restore"
      exit 0
    fi
    tmp=$(mktemp)
    jq -s '.[0] * .[1]' "$HOME/.claude/settings.json" "$LOCAL" > "$tmp" && mv "$tmp" "$HOME/.claude/settings.json"
    echo "restored $KEY ($(jq --arg k "$KEY" '.[$k] | length' "$LOCAL") entries) into settings.json"
    ;;
  show)
    [ -s "$LOCAL" ] && cat "$LOCAL" || echo "no $LOCAL yet — run: $0 save"
    ;;
  *)
    echo "usage: $0 clean|smudge|save|restore|show" >&2; exit 1
    ;;
esac
