# DFC log catalog & observability design

The once-and-for-all reference for **what the DFC stack logs, which lines matter, and how to
show them**. Built 2026-07-09 from a live Loki sweep of prod + a full source catalog of every
`logger.*` call in control-service / grid-gateway / dema-ops push engine.

Companion files: `tools/README.md` (query wrappers + telemetry SQL), `INVESTIGATIONS.md` (the
reasoning method for anomalies), `grafana/` (importable dashboard + derived-fields config).

---

## TL;DR — the decision

**Grafana-first, three layers. No new debugging UI is needed** — the data model for the
"click a command → supervisor allocations → miner allocations" drill-down **already exists in
structured log fields** and stitches together perfectly by `request_id`. What's missing is
*curation* (a noise-free activity view) and *linking* (Grafana derived fields), not
instrumentation.

| Layer | What it is | How | Volume |
|---|---|---|---|
| **1. Activity Log** | "what happened & why" — every site-level state change (dispatch, sleep/wake, override, clamp, fault) | one curated LogQL stream on the `module` label (below) | **~8 lines/hour** |
| **2. Dispatch drill-down** | click a `request_id` → fleet `power_allocations` → supervisor `miner_targets` → per-miner `target_wattage` | Grafana **derived fields** make ids clickable; the fields are already logged | on demand |
| **3. Noise floor** | per-cycle health/comms churn, heartbeats | module-scoped, on-demand only | ~30k lines/hour |

The dashboard's operator "activity feed" should be **fed by the same Layer-1 event stream** (via
Loki API or by mirroring these EVENT lines to a small table), not reinvented.

The remaining work is a short list of **instrumentation gaps** (§6) — mostly *adding a
correlation id to the origin and the autonomous-recovery path*, and *logging the DemaOps schedule
mutations at all*.

---

## 1. Log architecture (how a line is shaped)

- **Emitters → Loki:** `control_service` and `grid-gateway` push directly to Loki via
  `loki_logger_handler` (`src/core/logging.py`). `discovery_service` also flows now.
  **`dema-ops-backend` does NOT reach Loki** — it renders structlog JSON to stdout only
  (Docker `json-file`). So the *origin* of every curtailment is currently **invisible in Loki**
  (gap G3).
- **The only Loki label that matters is `module`** (= the Python logger name). Other labels:
  `application`/`service_name` (∈ `control_service`, `grid-gateway`, `modbus_server`,
  `discovery_service`), `environment=production`, `cluster=mining_fleet`.
- **Everything else lives inside the JSON line body**, queryable with `| json` but NOT indexed:
  `request_id`, `supervisor_id`, `miner_ip`, `operation`, `target_power`, `level`, `function`,
  and structured dicts (`power_allocations`, `miner_targets`, `bypass_*`).
- **Context propagation:** `request_id`/`operation`/`target_power` are auto-injected on every
  control-service line in a dispatch's asyncio task via `contextvars` (`src/core/context.py`);
  `supervisor_id` is injected on every line from a SupervisorActor process. **grid-gateway and
  dema-ops have NO contextvar/correlation id** (gaps G1/G3).

### The `module` taxonomy (11 values) and live volume

| module | ~lines/h | role | dominant content |
|---|---|---|---|
| `miner` | ~15k | per-miner sensor loop + commands | health flap + comms timeouts (NOISE) + setpoint/sleep/wake EVENTs |
| `supervisor` | ~7k | per-breaker dispatch + breaker Modbus | `Power setpoint applied`, `Group power distribution completed` (miner_targets), breaker reads |
| `miner_client` | ~2.6k | Auradine HTTP client | `Giving up _call`, `Token rejected` (NOISE) |
| `_common` | ~2.6k | shared helpers | mixed |
| `supervisor_recovery` | ~1.2k | failure/recovery loop | redistribution EVENTs buried in health-notification NOISE |
| `grid_actor` | ~0.84k | **grid-gateway** DemaOps→fleet seam | ~100% the every-5s `command updated` + 30s `dispatch active` heartbeat (NOISE) |
| `breaker` | ~0.24k | recovery baseline capture | `Captured/Cleared breaker baseline` |
| `fleet` | ~0.24k | **FleetControllerActor** — the top of the drill-down | dispatch start/end EVENTs + health-notif NOISE |
| `control_api` | ~0 | HTTP command surface | (quiet) |
| `heartbeat`, `fbox_client` | low | liveness / FBOX HTTP | |

`fleet` + `grid_actor` are tiny and almost entirely where the **site-level story** lives — that's
why the activity log scopes to them.

---

## 2. The request_id taxonomy (the join key) — FOUR prefixes

Every command path stamps a short id that propagates to **every** downstream line
(one real dispatch = ~1,700 lines across fleet→supervisor→miner all sharing the id).

| Prefix | Origin | Meaning | Traceable? |
|---|---|---|---|
| `sfp-` | `set_fleet_power` | a real fleet power dispatch (from a DemaOps `setpoint` command, or manual) | ✅ full chain |
| `sac-` | `sleep_all_controllable` | curtailment (sleep everything) | ✅ full chain |
| `wac-` | `wake_all_controllable` | wake everything (undocumented in CLAUDE.md — gap) | ✅ full chain |
| `sup-` | supervisor-direct recovery calls | **autonomous** failure-recovery / rebalance | ⚠️ partial |

> **`sup-` is the one to watch.** It's the autonomous failure-recovery / surplus-redistribution
> path that **raced and defeated the 20:45 curtailment on 2026-07-07** (devlog
> `claude_2026-07-07-curtailment-defeated-by-surplus-redistribution.md`; it fired again
> 2026-07-09 08:45). It bypasses the cooldown and the in-flight lock, and the **fleet-level**
> surplus lines (`Surplus power redistribution targets calculated`, `Fleet-wide surplus power
> redistribution completed`) carry **NO request_id at all** — only the supervisor-direct
> `set_power_setpoint` calls get a `sup-` id (gap G2). An activity log that surfaces `sac-` and
> `sup-` side by side makes that incident obvious at a glance.

---

## 3. Query cheat-sheet (Loki)

- **Use backticks for line filters, never double-quotes:** `|= \`sfp-9b3a720c\``.
  Double-quoted filters through the URL-encoding path silently returned zero rows in testing.
- Everything downstream of a dispatch: `{application="control_service"} |= \`<request_id>\``
  (backticks) → the whole chain in one query.
- One breaker's story: `{module="supervisor"} |= \`container_06_breaker_2\``
  (supervisor_id is the breaker's device id; it's a line field, matched as a substring).
- Volume/edges beat pulling lines (5000-line cap): `tools/loki-count.sh` or
  `sum by (module) (count_over_time({environment="production"}[1h]))`.
- **`module` is the primary noise lever.** Scope to `fleet`/`grid_actor` for the story; add
  `!= \`<noise phrase>\`` to drop heartbeats.

### The Activity Log query (validated: ~198 lines / 24h, every one meaningful)

```logql
{module=~`fleet|grid_actor`}
  != `command updated`                 # drop the every-5s held-command echo (720/h noise)
  != `dispatch active`                 # drop the 30s "still holding" heartbeat
  != `health failure notification`     # drop per-miner health flap forwarded to fleet
  != `health recovery notification`
```

Returns exactly the site-level state changes: `Subtracting uncontrollable draw` +
`Fleet power distribution completed` (dispatches), `Sleep-all requested/completed`,
`Dispatch applied: setpoint/sleep` (gateway), `Power setpoint requested` / `Wrote normal
setpoint to input register` (ETP writes), `Surplus power redistribution *` (autonomous),
`Scheduler setpoint … exceeds controller max` (clamp), `Runtime power_setpoints_enabled update
applied` (config change), and `Site meter reads below sum of breakers` (fault). Add
`supervisor_recovery` redistribution EVENTs as a secondary panel if you want the recovery detail.

---

## 4. Event catalog (EVENT-tier lines — the ones to surface)

Grouped by the story an operator reads. Fields listed are the useful line-body keys.
(Full 213-line catalog incl. OPERATIONAL/DIAGNOSTIC/NOISE lives in the workflow output; this is
the EVENT subset.)

### 4a. A command enters the fleet (origin → gateway → fleet)
| module | message | level | key fields | answers |
|---|---|---|---|---|
| grid_actor | `Dispatch applied: setpoint (N.N MW)` / `… sleep` | INFO | `bypass_command_kind, bypass_setpoint_mw, bypass_etp` | gateway forwarded a DemaOps command to the fleet |
| grid_actor | `Power setpoint requested (normal mode): N.N MW` / `Wrote normal setpoint to input register` | INFO | mw | ETP-series setpoint write (non-bypass path) |
| grid_actor | `DemaOps command updated: BypassCommand(...)` | INFO | — | **NOISE** (every 5s, unchanged) — demote to DEBUG (G4) |
| grid_actor | `DemaOps dispatch active — … for Ns (ETP bypassed)` | INFO | `bypass_*_, bypass_age_s, reason` | **NOISE floor** (30s heartbeat) but the ONLY place the held command + its age is visible |

### 4b. The fleet dispatches (the drill-down anchor)
| module | message | level | key fields | answers |
|---|---|---|---|---|
| fleet | `Subtracting uncontrollable draw from fleet target` | INFO | `request_id, total_power, uncontrollable_draw, controllable_target, site meter` | dispatch START: what target, what the meter said |
| fleet | `Fleet power distribution completed` | INFO | `request_id, strategy, dispatch_seconds, target_power, total_power, **power_allocations** (sup→W), successful_supervisors, total_supervisors` | dispatch END + **per-supervisor allocation dict** |
| fleet | `Sleep-all requested — dispatching 0 to every supervisor` / `Sleep-all completed` | INFO | `request_id (sac-)` | curtailment start/end |
| fleet | `Command {cmd} rejected: a fleet dispatch is already in flight` | WARNING | — (**no request_id** — G1) | in-flight-lock rejection |
| fleet | dispatch rejections (over global limit / unreachable supervisor / projected-cap / infeasible-range) | WARNING/ERROR | reason | why a command did nothing (Loki-only today — G5) |
| supervisor | `Scheduler setpoint N.N MW exceeds controller max N.N MW` | WARNING | | a command was **clamped** to capacity |

### 4c. Per-supervisor & per-miner (bottom of the drill-down)
| module | message | level | key fields | answers |
|---|---|---|---|---|
| supervisor | `Group power distribution completed` | INFO | `request_id, supervisor_id, **miner_targets** (IP→W)` | **per-miner allocation dict** for this breaker |
| supervisor | `Power setpoint applied` / `Failed to set power setpoint` | INFO/ERROR | `request_id, supervisor_id, miner_ip` | which miner got commanded / failed |
| miner | `Power setpoint set successfully` | INFO | `request_id, supervisor_id, miner_ip, target_wattage` | the exact watts landed on a miner |
| miner | `Miner put to sleep` / `Miner woken up successfully` | INFO | `request_id, miner_ip` | per-miner sleep/wake |
| miner | `Reconciled power_setpoint from hardware /mode — believed X hardware Y` | WARNING | `miner_ip` (**no request_id** — G2) | **the miner self-reverted** the setpoint (Auradine behavior) |

### 4d. Autonomous recovery / surplus (the `sup-` path — least traceable, most dangerous)
| module | message | level | key fields | answers |
|---|---|---|---|---|
| supervisor_recovery | `Miner failure detected - queuing for batch processing` | INFO | miner_ip, supervisor_id | a miner tripped the failure detector |
| supervisor_recovery | `Batch classification complete - proceeding with power redistribution` | INFO | supervisor_id | recovery is about to move power |
| supervisor_recovery | `Received health change notification for unregistered miner` | WARNING | miner_ip, supervisor_id | **anomaly** — ~810/3h; a miner sending health events not registered on that breaker |
| fleet | `Surplus power redistribution targets calculated` / `Fleet-wide surplus power redistribution completed` | INFO | `surplus_power` (**NO request_id** — G2) | the fleet re-commanded power autonomously |

### 4e. Faults / config the operator must not miss
| module | message | level | answers |
|---|---|---|---|
| fleet | `Site meter reads below sum of breakers — possible meter or breaker fault` | WARNING | **top live signal** — 146×/24h; VCB/meter under-read plausibility guard firing |
| fleet | `Runtime power_setpoints_enabled update applied` | INFO | a runtime config change to which miners are controllable |
| control_api | `control flip miners[N] -> enabled=… by=<user>` | WARNING | **operator audit** — who enabled/disabled which miners, and when (the controllability change trail) |
| miner | `Reconciled is_sleeping from hardware /mode — believed state had drifted` | WARNING | a miner self-slept or self-woke (state drift caught by the sensor reconcile) |
| grid_actor | site-meter forced to `None` on ETP heartbeat stall | — | **currently SILENT** (G5) — a stale-ETP meter dropout leaves no log |

---

## 5. Drill-down recipe (the "click a setpoint" feature)

Everything below is a filter on an id you already have from the activity log. **This is the
feature the dashboard wants — and it's already fully backed by logged fields for
`sfp-`/`sac-`/`wac-`.**

```
1. Site activity  → pick a `Fleet power distribution completed` line → copy its request_id (sfp-…)
2. Whole dispatch : {application="control_service"} |= `sfp-…`            (all ~1700 lines)
3. Supervisor split: {module="fleet"}      |= `sfp-…` |= `distribution completed`  → power_allocations{sup→W}
4. Miner split    : {module="supervisor"}  |= `sfp-…` |= `Group power distribution completed` → miner_targets{ip→W}
5. Per miner      : {module="miner"}        |= `sfp-…` |= `setpoint set successfully`         → miner_ip, target_wattage
6. Failures       : {module=~"supervisor|miner"} |= `sfp-…` |= `Failed`
```

In Grafana this becomes **one click** once derived fields are configured (§ grafana/).

---

## 6. Instrumentation gaps (ranked; each is a small PR)

These are the only things blocking a *complete* click-through story. Ordered by value.

- **G1 — Correlate the origin to the dispatch.** grid-gateway has no correlation id; a DemaOps
  command edge and the `sfp-` dispatch it triggers are linked only by timestamp. Thread a
  `schedule_command_id` from the gateway edge into `set_fleet_power`, or at least log the
  gateway's applied `(kind, watts)` edge **with** the resulting `request_id`. Also add a
  no-change guard so `DemaOps command updated` fires only on an edge (kills ~720/h noise — G4).
- **G2 — Give the `sup-` recovery/surplus path a request_id everywhere.** The fleet-level
  surplus lines carry none; the most dangerous autonomous behavior is the least traceable.
- **G3 — dema-ops-backend must log to Loki, and must log schedule mutations.** Add the Loki
  handler (mirror control-service). Log: layer enable/disable (the act that arms curtailment),
  override set (with watts + window, not just kind+by), the compiled command pushed + which
  layer won. Today the origin of curtailment is a black box in Loki.
- **G4 — Demote per-poll heartbeats** (`DemaOps command updated` every 5s; consider the 30s
  `dispatch active` → DEBUG with an edge-triggered INFO on change). ~100% of grid-gateway volume
  is this echo.
- **G5 — Turn silent gates & rejections into edge EVENTs:** site-meter ETP-gate flip
  (meter→None), `is_reachable`/`breaker_data_fresh` transitions (the G1 safety gate), dispatch
  rejections, transparent-hold (compile→None). These are the "why did nothing happen" answers.
- **G6 — Post-dispatch convergence check:** nothing logs whether the breaker actually reached
  the commanded target after the stagger window. A single "converged / missed by X" EVENT per
  dispatch would close the loop between commanded and observed.

---

## 7. Grafana setup (see `grafana/`) — DEPLOYED 2026-07-09

Both are **live in prod Grafana** (applied via the API as `admin`):

- **Dashboard** → http://10.100.20.15:3000/d/dfc-activity (Operations folder). Panels:
  stat row (dispatches / curtailments / autonomous-surplus / meter-fault / rejections),
  **Activity Log** (§3 query, `| json | line_format` → clean one-liners with request_id inline,
  meter-fault excluded to the Faults panel), **Faults** (surplus / reconcile-drift / rejection),
  **Dispatch drill-down** (a `request_id` textbox var → per-supervisor `power_allocations`,
  per-miner `miner_targets`, whole chain — all pretty-printed JSON), **Volume by module**.
  Verified end-to-end against `sfp-9b3a720c`. Mirror on disk: `grafana/dfc-activity-dashboard.json`.
- **Derived fields** on the Loki datasource make `request_id` / `supervisor_id` / `miner_ip`
  **clickable** in any log detail (single-highest-leverage change; the datasource had none).
  Mirror on disk: `grafana/loki-derived-fields.json`.

To re-import elsewhere or restore: POST `/api/dashboards/db` / PUT the datasource — both files are
ready. Any further change is a prod-Grafana write.
