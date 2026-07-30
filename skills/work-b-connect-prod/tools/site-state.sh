#!/usr/bin/env bash
# Fast site-health snapshot — "is the site awake / asleep / stuck, and is control healthy?"
# Runs the three sweeps used every monitoring tick, each SMALL + retry-once (the telemetry
# DB drops connections under load), with a data-freshness column so you never read a stale
# value as live.
#
# Usage:
#   site-state.sh            # loki error window = last 30 min
#   site-state.sh 60         # loki error window = last 60 min
#
# Reads (all read-only, time-bounded):
#   1. grid_state  (device_id=grid_actor)      — authority/mode/setpoint/override/emergency + age_s
#   2. fleet_state (device_id=fleet_controller) — meter/max/min/target in MW
#   3. grid-gateway ERROR / 'exceeds controller max' count (the over-max-wake-bug detector)
#
# Interpreting the output (see also ../SKILL.md "site state cheatsheet" + the
# prod-nightly-wake-setpoint-over-max memory):
#   - operating_mode=local  → SOVEREIGN (ETP bypassed): bypasses the over-max reject bug,
#                             but IGNORES OETC remote curtailments (compliance exposure).
#     operating_mode=remote → SERIES (ETP authoritative): honors OETC, but a schedule
#                             setpoint ABOVE the live max_power gets REJECTED (the stuck/self-wake bug).
#     (During a SERIES sleep, mode oscillates local<->remote every ~5min = the sleep re-propose. Normal.)
#   - awake:  meter ≈ target, max_power > meter (healthy separated envelope).
#   - asleep: meter ≈ min_power ≈ target (~1-2 MW cooling floor), max_power still ≫ meter.
#   - STUCK/collapsed (BUG): max_power == min_power == meter (envelope collapsed to the meter),
#                            and/or gateway spewing 'exceeds controller max'. Site is open-loop.
#   - etp_remote_override=True with a FROZEN _mw across minutes = STALE latch (inert under
#     sovereign), NOT a live OETC dispatch. A moving _mw = a real remote curtailment.
#   - age_s should be ~0-90. If age_s is large / query returns nothing, telemetry is stale —
#     suspect the telemetry consumer, not the fleet.
set -euo pipefail
cd "$(dirname "$0")"

MINS="${1:-30}"

# BSD (macOS) vs GNU date for the loki window
if date -u -v-1M >/dev/null 2>&1; then
  START="$(date -u -v-"${MINS}"M +%Y-%m-%dT%H:%M:%SZ)"
else
  START="$(date -u -d "${MINS} minutes ago" +%Y-%m-%dT%H:%M:%SZ)"
fi
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# retry-once wrapper: the telemetry DB intermittently closes the connection mid-query
_tq() {
  ./psql-telemetry.sh -c "$1" 2>/dev/null || { sleep 3; ./psql-telemetry.sh -c "$1"; }
}

echo "===== now: ${NOW} ====="

echo "----- grid_state (grid_actor) -----"
_tq "SELECT DISTINCT ON (response_key) response_key, response_value,
       round(extract(epoch FROM (now()-timestamp))) AS age_s
     FROM telemetry_data
     WHERE device_id='grid_actor' AND endpoint='grid_state'
       AND timestamp > now() - interval '120 seconds'
       AND response_key IN ('system_state','dispatch_authority','operating_mode',
           'power_setpoint_mw','etp_remote_override','etp_remote_override_mw',
           'grid_frequency_hz','emergency_ffr_type')
     ORDER BY response_key, timestamp DESC;"

echo "----- fleet_state (fleet_controller), MW -----"
_tq "SELECT DISTINCT ON (response_key) response_key,
       round(response_value::numeric/1e6,3) AS mw,
       round(extract(epoch FROM (now()-timestamp))) AS age_s
     FROM telemetry_data
     WHERE device_id='fleet_controller' AND endpoint='fleet_state'
       AND timestamp > now() - interval '120 seconds'
       AND response_key IN ('site_total_meter_wattage','max_power','min_power','site_total_target_wattage')
     ORDER BY response_key, timestamp DESC;"

echo "----- grid-gateway errors / over-max rejections (last ${MINS} min) -----"
./loki-count.sh '{application="grid-gateway"} |~ `(?i)error|exceeds controller max|latch|freeze`' \
  "${START}" "${NOW}" 5m 2>/dev/null || echo "(loki query failed)"
