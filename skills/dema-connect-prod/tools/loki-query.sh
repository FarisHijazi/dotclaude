#!/usr/bin/env bash
# Query prod Loki (10.100.20.15:3100) and print time-sorted "HH:MM:SS.mmm LEVEL message" lines.
#
# Usage:
#   loki-query.sh '<logql>' <start> <end> [limit] [--raw]
#
# Examples:
#   loki-query.sh '{application="control_service"} |= "sfp-"' 2026-07-04T14:20:00Z 2026-07-04T15:00:00Z
#   loki-query.sh '{application="control_service"} |= "sfp-" != "Token rejected"' 2026-07-04T14:20:00Z 2026-07-04T15:00:00Z 2000
#   loki-query.sh '{application="control_service"} | json | supervisor_id="sup_1"' ... (label filters work too)
#
# Notes:
#   - Loki labels: application/service_name in {control_service, grid-gateway, modbus_server}
#   - Result cap is 5000 lines per call; if you hit it, narrow the filter or time range
#     (the script warns when the cap is hit).
#   - --raw prints the full JSON log line instead of just level+message
#     (controller lines carry request_id, miner_ip, supervisor_id, target_power, ...).
set -euo pipefail

LOKI_URL="${LOKI_URL:-http://10.100.20.15:3100}"
QUERY="${1:?usage: loki-query.sh '<logql>' <start> <end> [limit] [--raw]}"
START="${2:?start time, e.g. 2026-07-04T14:20:00Z}"
END="${3:?end time, e.g. 2026-07-04T15:00:00Z}"
LIMIT="${4:-5000}"
RAW="${5:-}"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

curl -sf -G "$LOKI_URL/loki/api/v1/query_range" \
  --data-urlencode "query=$QUERY" \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode "limit=$LIMIT" \
  --data-urlencode "direction=forward" > "$TMP"

python3 - "$TMP" "$LIMIT" "$RAW" <<'EOF'
import json, sys, datetime
d = json.load(open(sys.argv[1]))
limit = int(sys.argv[2]); raw = sys.argv[3] == "--raw"
rows = []
for s in d["data"]["result"]:
    for ts, line in s["values"]:
        rows.append((int(ts), line))
rows.sort()
for ts, line in rows:
    t = datetime.datetime.fromtimestamp(ts / 1e9, datetime.UTC).strftime("%H:%M:%S.%f")[:-3]
    if raw:
        print(t, line)
        continue
    try:
        j = json.loads(line)
        print(t, j.get("level", "?"), j.get("message", line)[:300])
    except Exception:
        print(t, "-", line[:300])
if len(rows) >= limit:
    print(f"WARNING: hit the {limit}-line cap — output is truncated; narrow the query/range", file=sys.stderr)
EOF
