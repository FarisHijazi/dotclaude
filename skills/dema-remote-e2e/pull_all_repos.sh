#!/usr/bin/env bash
# Pull EVERY dema repo to latest before an e2e run — especially an ETP /
# grid_etp_test.py run, where a single stale repo silently breaks the whole
# suite (cross-repo register lockstep: modbus-server <-> virtual-etp <->
# grid-gateway). A stale checkout looks exactly like a code regression but is
# not — this bit 3x in one session (2026-07-19). See SKILL.md + memory
# project_etp_modbus_register_lockstep / project_etp_plc_reboot_quirk.
#
# Usage (run ON the e2e host: buzastation / dema-dev / dema-ahmed-dev):
#   bash pull_all_repos.sh            # ff-only pull each repo's CURRENT branch (non-destructive)
#   bash pull_all_repos.sh --master   # switch every CLEAN repo to master, then pull
#
# --master will NOT touch a repo with uncommitted changes (it's skipped, loudly)
# so a feature branch you're mid-editing is never clobbered. Default mode never
# switches branches at all — it just brings whatever you're on up to its upstream.
#
# Always eyeball the final table: every repo NOT under test should read `master`
# and `up-to-date`.
set -uo pipefail

# The dema repos root differs per host.
ROOT=""
for cand in "$HOME/Projects/dema" "$HOME/Projects/demaenergy.d"; do
  [ -d "$cand" ] && ROOT="$cand" && break
done
if [ -z "$ROOT" ]; then
  echo "ERROR: no dema repos root found (~/Projects/dema or ~/Projects/demaenergy.d)" >&2
  exit 1
fi
echo "== dema repos root: $ROOT =="

TO_MASTER=0
[ "${1:-}" = "--master" ] && TO_MASTER=1

declare -a SUMMARY

for repo in "$ROOT"/*/; do
  [ -d "$repo/.git" ] || continue
  name="$(basename "$repo")"
  cd "$repo" || continue

  git fetch --quiet --all --prune 2>/dev/null

  dirty=""
  [ -n "$(git status --porcelain)" ] && dirty="dirty"

  if [ "$TO_MASTER" = "1" ] && [ -z "$dirty" ]; then
    git checkout --quiet master 2>/dev/null || true
  fi

  branch="$(git rev-parse --abbrev-ref HEAD)"

  # Only fast-forward — never merge/rebase automatically.
  pull_out="$(git pull --ff-only --quiet 2>&1)"; pull_rc=$?
  if [ $pull_rc -ne 0 ]; then
    state="PULL-FAILED (${pull_out//$'\n'/ })"
  elif [ -n "$dirty" ]; then
    state="up-to-date (DIRTY — not switched)"
  else
    state="up-to-date"
  fi

  sha="$(git rev-parse --short HEAD)"
  SUMMARY+=("$(printf '%-24s %-40s %-10s %s' "$name" "$branch" "$sha" "$state")")
done

echo
echo "== repo state after pull =="
printf '%-24s %-40s %-10s %s\n' "REPO" "BRANCH" "SHA" "STATE"
for line in "${SUMMARY[@]}"; do echo "$line"; done
echo
echo "NOTE: before an ETP/grid_etp run, every repo NOT under test should read 'master'."
