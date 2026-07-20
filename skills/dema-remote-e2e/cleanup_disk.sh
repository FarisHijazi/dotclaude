#!/usr/bin/env bash
# Reclaim Docker disk on an e2e host. Repeated e2e runs pile up build cache,
# dangling images, dead containers, and unbounded logs — on 2026-07-05 this
# filled / to 100% on dema-ahmed-dev and silently took the GitHub runner offline
# (it crash-loops on "No space left on device").
#
# Usage (run ON the e2e host: buzastation / dema-dev / dema-ahmed-dev):
#   bash cleanup_disk.sh           # safe: prune only UNUSED docker artifacts
#   bash cleanup_disk.sh --fresh   # also tear the dfc stack down (-v) first
#
# Note: dema-ahmed-dev already runs this automatically (weekly + a 6h emergency
# prune at 85% + logrotate). This script is for the other hosts / manual runs.
set -uo pipefail

RAY_HEAD="${RAY_HEAD_DIR:-$HOME/Projects/dema/ray-head}"
[ -d "$RAY_HEAD" ] || RAY_HEAD="$HOME/Projects/demaenergy.d/ray-head"

echo "== disk before =="; df -h / | tail -1

if [ "${1:-}" = "--fresh" ] && [ -d "$RAY_HEAD" ]; then
  echo "== tearing down dfc stack ($RAY_HEAD) =="
  (cd "$RAY_HEAD" && sudo docker compose down -v --remove-orphans) || true
fi

echo "== pruning docker (unused only; running stack untouched) =="
sudo docker container prune -f
sudo docker image prune -af
sudo docker buildx prune -af      # buildx, not builder — containerd image store
sudo docker network prune -f

# Truncate any container log over 50M (running containers keep logging).
for f in $(sudo du /var/lib/docker/containers/*/*-json.log 2>/dev/null | awk '$1>51200{print $2}'); do
  sudo truncate -s 0 "$f"
done

echo "== disk after =="; df -h / | tail -1
