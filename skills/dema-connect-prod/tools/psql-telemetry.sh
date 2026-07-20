#!/usr/bin/env bash
# READ-ONLY psql into the prod telemetry TimescaleDB (10.100.20.16/telemetry, ~250 GB).
# Safety baked in:
#   - session is forced read-only (default_transaction_read_only=on) — writes error out
#   - statement_timeout=120s — a bad plan cancels itself instead of hanging/loading the DB
#
# ⚠️ EVERY query MUST have a bounded time predicate (WHERE timestamp BETWEEN ...).
#    An unfiltered scan reads the whole hypertable and can crash the DB.
#
# Usage:
#   psql-telemetry.sh -c "SELECT ... WHERE timestamp BETWEEN '...' AND '...' ..."
#   psql-telemetry.sh -f query.sql
#   psql-telemetry.sh            # interactive (still read-only)
#
# See tools/README.md for the telemetry_data schema + proven query recipes.
set -euo pipefail
export PGPASSWORD=nAzR8lmCrWwoa3
export PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=120000"
exec psql -h 10.100.20.16 -U telemetry_user -d telemetry "$@"
