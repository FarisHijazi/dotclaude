#!/usr/bin/env bash
# Lists icon files whose name matches every word given, e.g. `find.sh database` or `find.sh postgres`.
set -euo pipefail
cd "$(dirname "$0")"
[ -d brands ] || ./fetch.sh >/dev/null
files=$(find brands/svg lucide tabler devicon/svg -name '*.svg' | sort)
for word in "$@"; do files=$(grep -i -- "$word" <<<"$files" || true); done
head -60 <<<"$files"
