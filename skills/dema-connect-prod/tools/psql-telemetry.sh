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
# --- credentials -------------------------------------------------------------
# Read from the environment, never committed: this repo is PUBLIC, and these two
# scripts previously carried the live passwords as literals. Put them in
# ~/.config/dema/prod.env (chmod 600). There is deliberately NO default — a fallback
# would put the credential straight back into git.
[ -f "${DEMA_ENV_FILE:-$HOME/.config/dema/prod.env}" ] && . "${DEMA_ENV_FILE:-$HOME/.config/dema/prod.env}"
: "${DEMA_TELEMETRY_DB_PASSWORD:?not set. Put it in ~/.config/dema/prod.env (chmod 600) or export it.}"
export PGPASSWORD="${DEMA_TELEMETRY_DB_PASSWORD}"
export PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=120000"
exec psql -h "${DEMA_TELEMETRY_DB_HOST:-10.100.20.16}" -U "${DEMA_TELEMETRY_DB_USER:-telemetry_user}" -d "${DEMA_TELEMETRY_DB_NAME:-telemetry}" "$@"
