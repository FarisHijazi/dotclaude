#!/usr/bin/env bash
# READ-ONLY psql into the prod control config DB (10.100.20.16/control).
# Small DB (devices, miner_config, supervisor_config_current, ...) — safe to query freely,
# but the session is still forced read-only + 60s statement timeout as a guard rail.
# All WRITES must go through the discovery-service API, never direct SQL.
#
# Usage:
#   psql-control.sh -c "SELECT * FROM miner_config_current LIMIT 5"
#
# Gotchas:
#   - miner_config.device_id is an INTEGER, not the miner serial number.
#     Serial↔location mapping lives in the TELEMETRY db table miner_tank_mapping
#     (serial ↔ container_name/tank/breaker/phase) — see psql-telemetry.sh.
#   - miner_config is append-only; per-IP dedup: DISTINCT ON (ip) ... ORDER BY ip, created_at DESC
set -euo pipefail
export PGPASSWORD=btjkIvKCpVj9YD
export PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=60000"
exec psql -h 10.100.20.16 -U control_writer -d control "$@"
