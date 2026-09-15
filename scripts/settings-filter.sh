#!/usr/bin/env bash
# Keep machine-local keys of settings.json out of git, without untracking the file.
#
# Two kinds of per-machine state live inside an otherwise-shared file:
#
#   enabledPlugins           which plugins THIS box has installed and switched on
#   env                      per-machine environment (a local proxy's base URL, and
#                            anything else that is true here and nowhere else)
#   extraKnownMarketplaces   mostly shared, but a few marketplaces belong to one
#                            machine only (a work marketplace on that work's VM)
#
# Neither can simply be moved somewhere untracked: there is no user-level
# settings.local.json — Claude Code reads project-local overrides at the project
# scope, but user-scope settings come only from ~/.claude/settings.json.
#
# A git filter is the mechanism for exactly this:
#   clean  (worktree -> index)  strips enabledPlugins, and any marketplace this
#                               machine has marked private
#   smudge (index -> worktree)  merges THIS machine's copy of both back in
#
# Marketplaces are shared BY DEFAULT; a machine opts one out with `privatize`.
# That direction matters: a session that cannot resolve a marketplace rewrites
# settings.json without it, so an un-privatized work marketplace would be pruned
# for every machine at once.
#
# Filters are per-clone by design (a repo cannot configure its own), so run
# scripts/install-git-filters.sh once on each machine. See also
# scripts/apply-overrides.sh, which solves the mirror-image problem for the
# untracked ~/.claude.json.
#
#   settings-filter.sh clean | smudge     (git calls these; stdin -> stdout)
#   settings-filter.sh save               snapshot the live keys into the local file
#   settings-filter.sh restore            merge the local file back into settings.json
#   settings-filter.sh show               print what the local file holds
#   settings-filter.sh privatize <name>   keep marketplace <name> on this machine only
#   settings-filter.sh share <name>       undo that; <name> syncs again
set -euo pipefail

LOCAL="${CLAUDE_SETTINGS_LOCAL:-$HOME/.claude/settings.plugins.local.json}"
SETTINGS="${CLAUDE_SETTINGS_FILE:-$HOME/.claude/settings.json}"
KEY=enabledPlugins
ENVK="env"
MK=extraKnownMarketplaces
PRIV=privateMarketplaces

command -v jq >/dev/null 2>&1 || { [ "${1:-}" = clean ] || [ "${1:-}" = smudge ] && cat; exit 0; }

# Names this machine has marked private, as a JSON array (empty if none).
# PRIV is the authoritative list: a name can be marked private before the
# marketplace is installed here, in which case there is no value to cache yet.
private_names() {
  [ -s "$LOCAL" ] || { echo '[]'; return; }
  jq -c --arg mk "$MK" --arg pn "$PRIV" '((.[$pn] // []) + ((.[$mk] // {}) | keys)) | unique' "$LOCAL"
}

case "${1:-}" in
  clean)
    jq --arg k "$KEY" --arg e "$ENVK" --arg mk "$MK" --argjson priv "$(private_names)" '
      del(.[$k]) | del(.[$e])
      | if has($mk)
        then .[$mk] |= with_entries(select(.key as $n | $priv | index($n) | not))
        else . end
    '
    ;;
  smudge)
    if [ -s "$LOCAL" ]; then
      # Merge ONLY the two keys this filter owns. A blind `.[0] * .[1]` would
      # also copy the bookkeeping list into settings.json, and would inject an
      # empty marketplace entry for a name marked private before it is installed.
      jq -s --arg k "$KEY" --arg e "$ENVK" --arg mk "$MK" '
        .[0] as $in | .[1] as $loc
        | $in
        | (if ($loc[$k] // {}) != {} then .[$k] = $loc[$k] else . end)
        | (if ($loc[$e] // {}) != {} then .[$e] = (($in[$e] // {}) + $loc[$e]) else . end)
        | (if ($loc[$mk] // {}) != {} then .[$mk] = (($in[$mk] // {}) + $loc[$mk]) else . end)
      ' - "$LOCAL"
    else
      cat
    fi
    ;;
  save)
    # NEVER clobber a good snapshot with an empty one. On a machine that has just
    # pulled, settings.json has no enabledPlugins yet (the filter was not
    # installed when git wrote it) — saving then would wipe the very thing we are
    # about to restore.
    live=$(jq --arg k "$KEY" '.[$k] | length' "$SETTINGS")
    if [ "$live" -eq 0 ] && [ -s "$LOCAL" ]; then
      echo "settings.json has no $KEY; keeping the existing $LOCAL ($(jq --arg k "$KEY" '.[$k] | length' "$LOCAL") entries)"
      exit 0
    fi
    # Private marketplaces: refresh the value of every name already marked
    # private, keeping the old value for one settings.json no longer carries.
    # Never promote a new name — that is what `privatize` is for.
    tmp=$(mktemp)
    jq -n --arg k "$KEY" --arg e "$ENVK" --arg mk "$MK" --arg pn "$PRIV" \
      --slurpfile s "$SETTINGS" \
      --argjson old "$([ -s "$LOCAL" ] && cat "$LOCAL" || echo '{}')" '
      ($old[$mk] // {}) as $cached
      | ($old[$pn] // []) as $names
      | {($k): ($s[0][$k] // {})}
      + (if (($s[0][$e] // {}) | length) > 0 then {($e): $s[0][$e]} else {} end)
      + (if ($names | length) > 0 then {($pn): $names} else {} end)
      + (($names | map({key: ., value: (($s[0][$mk] // {})[.] // $cached[.])})
          | map(select(.value != null)) | from_entries) as $vals
         | if ($vals | length) > 0 then {($mk): $vals} else {} end)
    ' > "$tmp" && mv "$tmp" "$LOCAL"
    echo "saved $KEY ($live entries)$(jq --arg mk "$MK" -r 'if (.[$mk]//{}|length)>0 then " + \(.[$mk]|length) private marketplace(s): \(.[$mk]|keys|join(", "))" else "" end' "$LOCAL") -> $LOCAL"
    ;;
  restore)
    # Put the keys back into a settings.json that a checkout wrote without them.
    # Merges rather than checking the file out, so unrelated local edits survive.
    [ -s "$LOCAL" ] || { echo "no $LOCAL to restore from"; exit 0; }
    if [ "$(jq --arg k "$KEY" '.[$k] | length' "$SETTINGS")" -gt 0 ]; then
      echo "settings.json already has $KEY; nothing to restore"
      exit 0
    fi
    tmp=$(mktemp)
    jq -s --arg k "$KEY" --arg e "$ENVK" --arg mk "$MK" '
      .[0] as $in | .[1] as $loc
      | $in
      | (if ($loc[$k] // {}) != {} then .[$k] = $loc[$k] else . end)
      | (if ($loc[$e] // {}) != {} then .[$e] = (($in[$e] // {}) + $loc[$e]) else . end)
      | (if ($loc[$mk] // {}) != {} then .[$mk] = (($in[$mk] // {}) + $loc[$mk]) else . end)
    ' "$SETTINGS" "$LOCAL" > "$tmp" && mv "$tmp" "$SETTINGS"
    echo "restored $KEY ($(jq --arg k "$KEY" '.[$k] | length' "$LOCAL") entries) into settings.json"
    ;;
  privatize|share)
    name="${2:-}"
    [ -n "$name" ] || { echo "usage: $0 $1 <marketplace-name>" >&2; exit 2; }
    tmp=$(mktemp)
    if [ "$1" = privatize ]; then
      jq -n --arg mk "$MK" --arg pn "$PRIV" --arg n "$name" \
        --slurpfile s "$SETTINGS" \
        --argjson old "$([ -s "$LOCAL" ] && cat "$LOCAL" || echo '{}')" '
        (($s[0][$mk] // {})[$n]) as $val
        | $old
        | .[$pn] = ((.[$pn] // []) + [$n] | unique)
        | if $val != null then .[$mk] = ((.[$mk] // {}) + {($n): $val}) else . end
      ' > "$tmp" && mv "$tmp" "$LOCAL"
      echo "$name is now private to this machine (stripped on commit, restored on checkout)"
    else
      jq --arg mk "$MK" --arg pn "$PRIV" --arg n "$name" '
        .[$pn] = ((.[$pn] // []) - [$n])
        | if has($mk) then .[$mk] |= del(.[$n]) else . end
      ' "$LOCAL" > "$tmp" && mv "$tmp" "$LOCAL"
      echo "$name is shared again — it will be committed like any other marketplace"
    fi
    echo "run: git add --renormalize settings.json"
    ;;
  show)
    [ -s "$LOCAL" ] && cat "$LOCAL" || echo "no $LOCAL yet — run: $0 save"
    ;;
  *)
    echo "usage: $0 clean|smudge|save|restore|show|privatize <name>|share <name>" >&2; exit 1
    ;;
esac
