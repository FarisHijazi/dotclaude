#!/usr/bin/env bash
# Count matching prod-Loki log lines per time bucket (sums across streams).
# Great for seeing WHEN something happened without pulling every line
# (avoids the 5000-line query cap entirely).
#
# Usage:
#   loki-count.sh '<substring or logql>' <start> <end> [step]
#
# Examples:
#   loki-count.sh 'Power setpoint applied' 2026-07-04T14:31:00Z 2026-07-04T14:48:00Z 30s
#   loki-count.sh '{application="grid-gateway"} |= "heartbeat"' 2026-07-04T00:00:00Z 2026-07-04T06:00:00Z 5m
#
# A bare string arg is wrapped as: {application="control_service"} |= "<string>"
set -euo pipefail

LOKI_URL="${LOKI_URL:-http://10.100.20.15:3100}"
Q="${1:?usage: loki-count.sh '<substring or logql>' <start> <end> [step]}"
START="${2:?start}"
END="${3:?end}"
STEP="${4:-30s}"

case "$Q" in
  \{*) SELECTOR="$Q" ;;
  *)   SELECTOR="{application=\"control_service\"} |= \"$Q\"" ;;
esac

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

curl -sf -G "$LOKI_URL/loki/api/v1/query_range" \
  --data-urlencode "query=count_over_time($SELECTOR [$STEP])" \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode "step=$STEP" > "$TMP"

# NB: the JSON goes through a temp file, NOT a pipe — `python3 - <<EOF` takes its
# program from stdin, so a pipe into it would be silently swallowed by the heredoc.
python3 - "$TMP" <<'EOF'
import json, sys, datetime
d = json.load(open(sys.argv[1]))
tot = {}
for r in d["data"]["result"]:
    for ts, v in r["values"]:
        tot[ts] = tot.get(ts, 0) + int(float(v))
for ts in sorted(tot):
    print(datetime.datetime.fromtimestamp(ts, datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"), tot[ts])
print("total:", sum(tot.values()))
EOF
