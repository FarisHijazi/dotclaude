#!/usr/bin/env bash
# Searches every open icon set on Iconify, e.g. `find.sh postgres` or `find.sh database lucide,tabler`.
# Fetch one with: curl https://api.iconify.design/<set>/<name>.svg
set -euo pipefail
query=${1:?usage: find.sh <word> [sets]}
sets=${2:-logos,devicon,simple-icons,lucide,tabler}
curl -fsS "https://api.iconify.design/search?query=$(printf %s "$query" | jq -sRr @uri)&prefixes=$sets&limit=60" | jq -r '.icons[]'
