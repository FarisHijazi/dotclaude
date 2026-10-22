#!/usr/bin/env bash
# Downloads the icon libraries into this folder (ignored by git: ~70 MB of SVGs). Re-run to update.
set -euo pipefail
cd "$(dirname "$0")"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
get() { (cd "$tmp" && npm pack -q "$1@$2" >/dev/null && mkdir -p "$3" && tar -xzf ./*.tgz -C "$3" && rm ./*.tgz); }
get simple-icons 16.35.0 si        # ~3400 brand/tool logos (CC0; trademarks belong to their owners)
get lucide-static 1.61.0 lucide    # ~1700 generic line icons (ISC)
get @tabler/icons 3.49.0 tabler    # ~5900 outline + filled icons (MIT)
get devicon 2.17.0 devicon         # ~900 dev tool logos in colour (MIT)
rm -rf brands lucide tabler devicon
mkdir -p brands devicon
mv "$tmp/si/package/icons" brands/svg && mv "$tmp/si/package/data/simple-icons.json" brands/simple-icons.json
mv "$tmp/lucide/package/icons" lucide
mv "$tmp/tabler/package/icons" tabler
mv "$tmp/devicon/package/icons" devicon/svg && mv "$tmp/devicon/package/devicon.json" devicon/devicon.json
for d in brands/svg lucide tabler/outline tabler/filled; do echo "$d $(ls "$d" | wc -l)"; done
echo "devicon $(ls devicon/svg | wc -l) tools"
