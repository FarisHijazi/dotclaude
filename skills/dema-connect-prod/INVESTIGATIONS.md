# Playbook: investigating fleet/power anomalies in prod

Distilled from the 2026-07-04 power-curve investigation (devlog:
`demaenergy.d/docs/devlog/claude_2026-07-05-power-curve-dip-investigation.md`).
Tools, schemas, and SQL recipes live in `tools/README.md` — read it first; this file is the
*method*: how to reason, where each answer lives, and the traps.

## The core discipline

1. **Every feature of a curve gets attributed** — either to a `request_id` (exact watts,
   exact time) or to a named miner-side behavior. "Probably the miners" without a per-miner
   trace is not an answer; neither is "we sent a setpoint" without the logged wattage.
2. **Commanded vs observed are different worlds.** Σ setpoint flat while Σ actual moves ⇒
   miner-side. Setpoint moving ⇒ find who commanded it (request_id) — or discover the miner
   changed it itself (see reconcile fingerprint below).
3. **Absence of commands is evidence — but only after you prove you'd see them.** First show
   the dispatch's command lines ARE in Loki (step 3), then a silent gap proves the controller
   sent nothing during it. That one check converts "we think it wasn't us" into "it wasn't us".
4. **Baseline the noise before the event.** Errors that also occur at the same rate before
   the anomaly (e.g. the constant `"Giving up _call"` floor) cannot be its cause. Always run
   `loki-count.sh` over a pre-event window for comparison.
5. **Distribution kills or confirms whole hypothesis families at once.** Any per-miner effect,
   grouped by container/breaker/phase: uniform % everywhere ⇒ firmware/fleet-logic; clustered
   ⇒ physical (that breaker, tank, cooling loop). One GROUP BY replaces hours of guessing.
6. **Beware sample bias.** `ORDER BY device_id LIMIT 4` gave 4 already-awake miners and nearly
   missed the entire dip. Sample FROM the population that shows the effect (e.g. miners
   asleep before the event), and check more than one stratum.
7. **Never trust one clock.** Grafana axis = browser tz (Saudi UTC+3); site = UTC+4; miner
   dashboards = the miner's own drifted clock (seen ≈UTC+2:49); controller `asctime` in log
   JSON = container tz (seen UTC-7). Trust only Loki line timestamps (what `loki-query.sh`
   prints, UTC) and telemetry `timestamptz`. Anchor any third-party graph by matching
   on/off/step transitions against telemetry, never by reading its axis.

## Where each answer lives (evidence map)

| Question | Source | How |
|---|---|---|
| What dispatches ran? target, strategy, window, per-SUPERVISOR watts | Loki `"Subtracting uncontrollable draw"` (start: request_id, total_power, uncontrollable, site meter) + `"Fleet power distribution completed"` (end: strategy, dispatch_seconds, **`power_allocations` dict**) | `tools/loki-query.sh ... --raw` |
| Exact per-MINER setpoint commanded | supervisor msgs `"Miner targets calculated"` / `"Group power distribution completed"` → **`miner_targets` dict (IP → W)**; per-miner `"Power setpoint set successfully"` → `target_wattage` | filter `\|= "container_XX_breaker_Y"` or `\|= "<ip>"` |
| Everything one dispatch did | `\|= "sfp-xxxxxxxx"` — request_id propagates through the whole chain | one Loki query |
| One breaker's story | `\| json \| supervisor_id="container_XX_breaker_Y"` | Loki |
| Did commands land on time / fail? | count `"Power setpoint applied"`, `"Miner woken up"`, `"Failed to set"` per 30 s — even spread across exactly `dispatch_seconds` = clean | `tools/loki-count.sh` |
| What did miners actually DO? | telemetry `miner_state` (`actual_wattage`, `power_setpoint`, `is_sleeping`, `mhs_5s`), `summary` (`Elapsed` = uptime), `psu` (`PowerIn`, `Vin1`, `Temp1..3`) | `tools/psql-telemetry.sh`, recipes in README |
| Who/where is a miner? | logs = `miner_ip`; telemetry = **serial** (`device_id`). Map: `miner_tank_mapping` (serial→container/tank/breaker/phase); IP↔serial via golden `miner_list.csv` or by matching a just-commanded unique setpoint value | |
| Independent power cross-checks | miner-reported (`miner_state`) vs breaker Modbus (`breaker_reading` per supervisor) vs site meter (`grid_actor`/`fleet_state`) — three sources; disagreement locates the lie | telemetry |
| Ramp rate used | (controllable_target − Σ controllable actual at start) / dispatch_seconds; identical round W/s across dispatches (e.g. 80,000) ⇒ ramp-rate dispatch | derive |

Strategy semantics when reading `power_allocations`: `equal` ⇒ near-identical per supervisor;
`min_breaker_changes` ⇒ deliberately uneven (0…max) — unevenness there is design, not a bug.

## Standard walk (fleet anomaly)

0. **Skim the Activity Log first** (`LOG_CATALOG.md` §3 query: `{module=~"fleet|grid_actor"} !=
   …`) over the window — ~8 lines/h, every one a state change. It usually names the culprit
   dispatch/curtailment/fault before you pull a single detailed trace. **Prime suspect for a
   "fleet re-woke itself / defeated curtailment" report: the autonomous `sup-` surplus-
   redistribution path** (`Surplus power redistribution …`, `module=supervisor_recovery`
   redistribution EVENTs) — it bypasses the cooldown + in-flight lock and its fleet-level lines
   carry no request_id (see the 2026-07-07 devlog).
1. **Window**: convert the report/screenshot to UTC (discipline #7).
2. **Dispatch inventory** (Loki): all starts/ends in the window ± 2 h. Note request_ids,
   targets, strategies, windows. This alone often explains "weird" steps.
3. **Execution check** (Loki counts): commands evenly spread over the window, failures ≈ 0,
   then silence. Silence + later movement ⇒ miner-side (discipline #3).
4. **Fleet aggregate** (telemetry, 30 s buckets): Σ actual vs Σ setpoint vs #hashing/#drawing.
   Find where they diverge.
5. **Per-miner classification** (single-scan `FILTER` recipe): pre/peak/trough per device →
   label (dipped/held/slow) → **GROUP BY container** (discipline #5).
6. **Sample individuals** from each label (discipline #6): full trace, 1–2 min buckets. The
   shape names the mechanism (surge-then-throttle, slow tune, self-revert…).
7. **Rule-outs**, each one query: `Elapsed` continuous (no reboot); `Vin1` stable (no grid
   event); `Temp1..3` mild (no PSU-thermal); noise baselined (discipline #4).
8. **Write the timeline** with every feature attributed; devlog it before stopping.

For a single miner: same walk, but start from `miner_targets`/per-IP lines (evidence map
row 2) and the telemetry trace for its serial; anchor its dashboard clock first.

## Known miner-side behaviors (Auradine) — recognize, don't chase

- **Post-wake surge-then-throttle** (~30% of woken miners, uniform across containers): jump
  to setpoint within ~90 s → self-throttle to ≈ pre-sleep operating point, hashrate halved →
  re-tune up ~300 W/min. Fleet: peak → ~10% dip → slow crawl; convergence **10–15 min after
  the dispatch window ends**. Budget curtailment-recovery lead time for it.
- **Wake-time setpoint may not stick:** a setpoint written at/near wake can be silently
  reverted to the pre-sleep retained value ~10 min later. Fingerprint (WARNING):
  `"Reconciled power_setpoint from hardware /mode — believed X, hardware Y"` = the MINER
  changed it, not us — and nothing re-pushes the intended value afterwards.
- **Wake inrush:** PSU spike a few % over the limit for <2 min. Not sustained overshoot.
- **`"Token rejected, re-authenticating"` waves** (~1/woken miner) around mass wakes:
  miner web-API session churn. Noise.
- **Constant `"Giving up _call"` floor** (~40/30 s): fixed set of miners in local mode
  (`remote setting can't overwrite local setting`). Pre-existing; baseline it.
- Miner dashboards read Power ~5–10% above `miner_state.actual_wattage` (different
  measurement point), and 24 h views smooth a short sleep into a shallow "dip".

## Traps that cost real time (all hit on 2026-07-04/05)

- Loki returns max **5000 lines** — a flood (token-rejected wave) silently truncates your
  window. Check the last timestamp; count first, pull lines second.
- SQL: joined CTEs each scanning `telemetry_data` hang the planner 10+ min — single scan +
  `FILTER`. Also: `round()::numeric`, `NULLIF(response_value,'None')`, psu values carry unit
  suffixes (`"243.50V"`), control-DB `device_id` is an INTEGER ≠ serial.
- `python3 - <<EOF` swallows piped stdin (heredoc wins) — pass data via temp file (the
  `tools/` scripts already do this).
- Screenshot axis ≠ UTC; two different dashboards in one investigation had two different
  offsets. Anchor before interpreting (discipline #7).
