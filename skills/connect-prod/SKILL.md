---
name: connect-prod
description: Read-only investigation of the DFC production site — query the control and telemetry (TimescaleDB) databases, search Loki logs, and read live site state. Use when diagnosing production behaviour, checking fleet/grid state, or correlating a dispatch across services. Never writes to production.
---

feel free to read the production db but make sure to always filter by time, also never write to the production db, just investigate etc, feel free to connect to the production services (ssh dema-control-service, dema-telemetry, ...)


## Safety

- NEVER do anything destructive to the production environment, in the rare case where something destructive is needed, ask for explicit permission first.
- NEVER modify the production DB without double confirming for explicit permission first.
- shutdown hosts or stop services without asking for permission

## Hosts

```sh
Host dema-grid-gateway
  HostName 10.100.20.19
  User service

Host dema-discovery
  HostName 10.100.20.8
  User service

Host dema-telemetry
  HostName 10.100.20.21
  User service

Host dema-ray-head
  HostName 10.100.20.18
  User service

Host dema-control-service
  HostName 10.100.20.20
  User service

Host dema-dema-ops
  HostName 10.100.20.22
  User service

# only tinker tools scripts are used here no other reason to ssh here except for arp-scan and tinker-tools scripts
Host dema-dev-1
  HostName 10.100.20.77
  User service

# really try to avoid using this one unless strictly necessary and ask for explicit permission
Host dema-proxmox
  HostName 10.100.1.49
  User root
```

## What/where do the logs live? Read LOG_CATALOG.md

`LOG_CATALOG.md` in this skill dir is the once-and-for-all reference for the whole stack's
logging: the `module` taxonomy + live volumes, the FOUR request_id prefixes
(`sfp-`/`sac-`/`wac-`/`sup-`), the tiered EVENT catalog (which lines matter), the validated
**Activity Log** LogQL (`{module=~"fleet|grid_actor"} != …` ≈ 8 meaningful lines/h), the
**click-a-command drill-down** recipe (request_id → `power_allocations` → `miner_targets` →
per-miner `target_wattage` — already fully backed by logged fields), the noise floor, and the
ranked instrumentation gaps. `grafana/` has an importable dashboard + the Loki derived-fields
config (makes request_id clickable). Read it before designing any log view or dashboard.

## Investigating an anomaly? Read INVESTIGATIONS.md

For any "why did the power/fleet do X" question, follow `INVESTIGATIONS.md` in this skill dir:
the reasoning discipline (attribute every curve feature to a request_id or a named miner
behavior), the evidence map (which question is answered by which Loki message / telemetry
endpoint), the standard 8-step walk, known Auradine behaviors (post-wake dip, setpoint
self-revert), and the traps (clock drift, Loki line cap, planner hangs).

## Investigation tools (Loki + read-only DB) — use these first

`tools/` in this skill dir has tested wrappers for prod log/telemetry digging — prefer them over
ad-hoc curl/psql (they bake in read-only sessions, statement timeouts, and JSON pretty-printing):

- `tools/site-state.sh [loki_window_mins]` — **fast site-health snapshot: run this FIRST every
  monitoring tick.** One shot → grid_state (sovereign/series, setpoint, override, emergency, +`age_s`
  freshness) + fleet_state (meter/max/min/target MW) + the grid-gateway over-max/error count. Small,
  time-bounded, retries once on a dropped DB connection. Interpretation cheatsheet (awake/asleep/stuck,
  stale-latch, sovereign-vs-series) in the script header + `tools/README.md`. The recurring incident it
  catches is the over-max wake bug — see the `prod-nightly-wake-setpoint-over-max` memory.
- `tools/loki-query.sh '<logql>' <start> <end> [limit] [--raw]` — time-sorted log lines from Loki
  (`http://10.100.20.15:3100`; apps: `control_service`, `grid-gateway`, `modbus_server`)
- `tools/loki-count.sh '<substr or logql>' <start> <end> [step]` — per-bucket counts (beats the 5000-line cap)
- `tools/psql-telemetry.sh -c "..."` — telemetry TimescaleDB (10.100.20.16/telemetry). **Session is
  write-blocked** + 120s timeout, but ⚠️ you must still time-bound every query (~250 GB hypertable).
- `tools/psql-control.sh -c "..."` — control config DB (10.100.20.16/control), write-blocked.

Read `tools/README.md` before querying: it has the `telemetry_data` schema (key-value long format,
`device_id` = miner **serial**, logs use `miner_ip` instead), proven SQL recipes, and the gotchas
(single-scan `FILTER` instead of CTE joins — joined CTE scans hang the planner; `'None'` strings;
unit suffixes in `psu` values; `round()` needs `::numeric`).

## Deploy / env vars (CI/CD runners) — do NOT edit host `.env`

Prod env lives in each repo's GitHub **Environment `production-ibri-1`**, in the `ENV_FILE`
**variable** (not a secret). The CI/CD workflow (self-hosted runner) renders `ENV_FILE` → the
host `.env`, pulls from ghcr, and recreates the container. So:

- **Never edit the host `/home/service/<repo>/.env`** — it's overwritten next deploy. Change the
  `ENV_FILE` variable instead. (Also: the hosts have no ghcr login, so a manual `docker compose up`
  fails with `denied` / `No such image` — only the runner can deploy.)
- Read: `gh api repos/DEMAEnergy/<repo>/environments/production-ibri-1/variables/ENV_FILE --jq .value`
- Write: `gh variable set ENV_FILE --env production-ibri-1 --repo DEMAEnergy/<repo> < file`
  (stdin; there is no `--body-file`).
- Apply: `gh run rerun <last CI/CD run id> --repo DEMAEnergy/<repo>` (vars are read at run time).

> ⚠️ **Do NOT quote repo `CLAUDE.md` env tables as live values — they are CODE DEFAULTS and DIFFER
> from prod.** Two real sources, in order of authority:
> 1. **The running container's env = the ULTIMATE truth** (what the process actually loaded; may lag
>    a not-yet-redeployed `ENV_FILE`):
>    `ssh dema-control-service 'docker exec control-service-control-service-1 printenv | grep -i <VAR>'`
>    (control-service container name is `control-service-control-service-1`, NOT `control-service`.)
>    Do the same on each host (`dema-grid-gateway`, `dema-dema-ops`, …) for that service's container.
> 2. **The GitHub Environment `production-ibri-1` → `ENV_FILE` variable** = the desired/deployed
>    config (`gh api … ENV_FILE | grep`; needs the DEMAEnergy `gh` account — `gh auth switch` if 404).
>
> Confirmed LIVE in the control-service container (2026-07-21) where docs differ / matter:
> `FLEET_TARGET_RECONCILE_TOLERANCE_W=50000` (doc default 25000),
> `FLEET_SETPOINT_COOLDOWN_SECONDS=60` (doc default 10), `FLEET_TARGET_RECONCILE_INTERVAL=60`,
> `FLEET_DEFAULT_RAMP_RATE=83333.33` W/s (=5 MW/min), `FLEET_MAX_RAMP_RATE=500000`,
> `FLEET_DISPATCH_SECONDS=0`, `FLEET_VCB_SMOOTHING_WINDOW=15`, `FLEET_BREAKER_SMOOTHING_WINDOW=1`,
> `FLEET_TARGET_RECONCILE_STRATEGY=min_breaker_changes`.

## Mistakes I made (don't repeat)
- Quoted the CLAUDE.md *default* (`FLEET_TARGET_RECONCILE_TOLERANCE_W=25000`) as the live prod value
  during an investigation — prod is 50000. Always read `ENV_FILE` for real values (see box above).
- Edited the host `.env` directly to enable the poller — wrong; reverted. Use `ENV_FILE` + rerun.
- Tried `docker compose up` on the host to apply env — fails (no ghcr login).

## Prod DemaOps (`ssh dema-dema-ops`, 10.100.20.22)
- Backend `demaops-demaops-backend-1` → `http://10.100.20.22:8000`; DB is **external**
  (`10.100.20.16/demaops`, no local db container, no `psql` on host).
- Query/seed/mint-keys by running the app's repos inside the backend container:
  `docker cp x.py demaops-demaops-backend-1:/tmp/ && docker exec -w /app demaops-demaops-backend-1 uv run --no-sync python /tmp/x.py`.
- Controller reaches DemaOps at `http://10.100.20.22:8000` — NOT the dev name `demaops-backend:8000`.
- Prod controller has `ENABLE_POWER_SETPOINT=true`: enabling the schedule poller makes it act on
  the live schedule. Safe only when the schedule is transparent or miners have setpoints disabled.
