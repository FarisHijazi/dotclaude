# Prod investigation tools (read-only)

Battle-tested during the 2026-07-04 power-curve investigation
(see `demaenergy.d/docs/devlog/claude_2026-07-05-power-curve-dip-investigation.md`).

| Tool | What it does |
|---|---|
| `loki-query.sh '<logql>' <start> <end> [limit] [--raw]` | time-sorted log lines from prod Loki |
| `loki-count.sh '<substr or logql>' <start> <end> [step]` | per-bucket line counts (beats the 5000-line cap) |
| `psql-telemetry.sh -c "..."` | read-only psql → telemetry TimescaleDB (write-blocked, 120s timeout) |
| `psql-control.sh -c "..."` | read-only psql → control config DB (write-blocked, 60s timeout) |

All timestamps are UTC. Site local time = UTC+4 (Asia/Muscat); Grafana in a Saudi browser shows UTC+3.

## Loki (http://10.100.20.15:3100)

> For the full event catalog, module taxonomy, the Activity-Log query, and the drill-down
> recipe, read `../LOG_CATALOG.md`. This section is the query mechanics only.

- Labels: `application` / `service_name` ∈ `control_service`, `grid-gateway`, `modbus_server`,
  **`discovery_service`**; plus **`module`** (the Python logger name — the ONLY useful
  content label: `fleet`, `supervisor`, `supervisor_recovery`, `miner`, `miner_client`,
  `breaker`, `grid_actor`, `control_api`, `heartbeat`, `fbox_client`, `_common`). Scope by
  `module` to cut noise — it's the primary lever. Also `environment=production`, `cluster`.
- Controller log lines are JSON with structured fields: `request_id`, `operation`,
  `target_power`, `supervisor_id`, `miner_ip`, `module`, `function`, and structured dicts
  (`power_allocations`, `miner_targets`, `bypass_*`). Only `module` is indexed; the rest are in
  the line body (`| json` to filter, or just `|= \`substr\``).
- **FOUR request_id prefixes:** `sfp-` (set_fleet_power), `sac-` (sleep_all), `wac-` (wake_all),
  `sup-` (autonomous recovery/surplus — the dangerous, only-partially-traced path). An id
  propagates to ALL ~1700 lines of its dispatch.
- **⚠️ Use backticks for line filters, not double-quotes:** `|= \`sfp-9b3a720c\``. A
  double-quoted filter through the URL-encoding path silently returned zero rows in testing.
- **`dema-ops-backend` does NOT push to Loki** (stdout only) — the *origin* of every curtailment
  is invisible in Loki today. Read its schedule/override activity from the backend container or
  the demaops DB, not Loki.
- **Miners are identified by `miner_ip` in logs, but by SERIAL NUMBER (`device_id`) in telemetry.**
- Query cap is 5000 lines — for "how many/when" questions use `loki-count.sh` instead of pulling lines.

### The Activity Log (site-level "what happened", ~8 meaningful lines/h)

```
{module=~`fleet|grid_actor`} != `command updated` != `dispatch active` \
  != `health failure notification` != `health recovery notification`
```

### Drill-down (click a command → allocations)

```
whole dispatch : {application="control_service"} |= `sfp-…`
per-supervisor : {module="fleet"}     |= `sfp-…` |= `distribution completed`        → power_allocations
per-miner      : {module="supervisor"} |= `sfp-…` |= `Group power distribution completed` → miner_targets
miner value    : {module="miner"}      |= `sfp-…` |= `setpoint set successfully`    → target_wattage
```
- High-signal dispatch messages: `"Subtracting uncontrollable draw from fleet target"`
  (start of set_fleet_power: total_power, uncontrollable_draw, controllable_target, request_id) and
  `"Fleet power distribution completed"` (end: strategy, dispatch_seconds, per-breaker power_allocations).
  Per-miner: `"Power setpoint applied"`, `"Miner woken up successfully"`, `"Miner put to sleep"`,
  `"Failed to set power setpoint"`.
- Known noise: constant background `"Giving up _call"` (~40 per 30s, miners in local mode:
  `"remote setting can't overwrite local setting"`) and `"Token rejected, re-authenticating"`
  waves after mass wakes — neither implies a dispatch problem by itself.

## Telemetry DB (10.100.20.16/telemetry, TimescaleDB, ~250 GB)

**⚠️ Every query MUST be time-bounded** (`WHERE timestamp BETWEEN … AND …`). The wrapper adds a
120s statement timeout but the time filter is still on you.

`telemetry_data` is key-value long format:
`(timestamp, device_id, endpoint, response_key, response_value TEXT)`.

- `device_id`: miner **serial** (e.g. `06000002A1`), or `container_XX_breaker_Y`,
  `fleet_controller`, `grid_actor`.
- Miner endpoints/keys (per sensor cycle, ~1/min per miner, 2879 miners):
  - `miner_state`: `actual_wattage`, `power_setpoint`, `is_sleeping`, `mhs_5s`,
    `is_healthy`, `consecutive_failures`, `power_setpoint_error`
  - `summary`: `Wattage`, `MHS 5s`, `Elapsed` (miner uptime — detects reboots), `Accepted`, `Rejected`
  - `psu`: `PowerIn`, `Vin1`, `Temp1..3`, `FanSpeed1..2` — **values carry unit suffixes**
    (`"243.50V"`): strip with `regexp_replace(response_value,'[^0-9.-]','','g')::float`
- Supervisor endpoints: `breaker_reading`, `supervisor_phase_a/b/c`, `supervisor_state`.
- `miner_tank_mapping` (serial → container_name/tank/breaker/phase) = the location join table.

### Query gotchas (each cost real time once)

- `round(float, 2)` doesn't exist → cast: `round((x)::numeric, 2)`.
- `response_value` can be the string `'None'` → `NULLIF(response_value,'None')::float`.
- **Do NOT join multiple CTEs that each scan `telemetry_data`** — the planner picks a
  disastrous plan and it hangs for 10+ min. Scan ONCE and split with
  `avg(w) FILTER (WHERE ts < '…')` conditional aggregation.

### Proven recipes

Fleet-wide power aggregate per 30s (Σ actual vs Σ setpoint vs miners hashing):

```sql
WITH m AS (
  SELECT time_bucket('30 seconds', timestamp) tb, device_id,
         avg(CASE WHEN response_key='actual_wattage' THEN NULLIF(response_value,'None')::float END) watt,
         avg(CASE WHEN response_key='power_setpoint' THEN NULLIF(response_value,'None')::float END) sp,
         avg(CASE WHEN response_key='mhs_5s'         THEN NULLIF(response_value,'None')::float END) mhs
  FROM telemetry_data
  WHERE timestamp BETWEEN '2026-07-04T14:30:00Z' AND '2026-07-04T14:48:00Z'
    AND endpoint='miner_state'
    AND response_key IN ('actual_wattage','power_setpoint','mhs_5s')
  GROUP BY 1,2)
SELECT tb, count(*) miners,
       round((sum(watt)/1e6)::numeric,2) sum_actual_mw,
       round((sum(sp)/1e6)::numeric,2)   sum_sp_mw,
       count(*) FILTER (WHERE mhs>0) hashing,
       count(*) FILTER (WHERE watt>100) drawing
FROM m GROUP BY tb ORDER BY tb;
```

Classify per-miner behavior across event windows in ONE scan (the no-hang pattern),
then locate by container via `miner_tank_mapping`:

```sql
WITH raw AS (
  SELECT device_id, timestamp ts, NULLIF(response_value,'None')::float w
  FROM telemetry_data
  WHERE timestamp BETWEEN '<t0>' AND '<t3>'
    AND endpoint='miner_state' AND response_key='actual_wattage'
), per AS (
  SELECT device_id,
    avg(w) FILTER (WHERE ts < '<t1>')                 pre,
    avg(w) FILTER (WHERE ts BETWEEN '<t1>' AND '<t2>') peak,
    avg(w) FILTER (WHERE ts >= '<t2>')                 trough
  FROM raw GROUP BY 1)
SELECT m.container_name, count(*) FILTER (WHERE trough < 0.75*peak) dipped, count(*) total
FROM per JOIN miner_tank_mapping m ON m.serial = per.device_id
GROUP BY 1 ORDER BY 1;
```

## Control DB (10.100.20.16/control) — small, safe to query freely

`miner_config` append-only (`device_id` INTEGER ≠ serial); current view `miner_config_current`;
dedup per IP with `DISTINCT ON (ip) … ORDER BY ip, created_at DESC`. Writes ONLY via
discovery-service API.
