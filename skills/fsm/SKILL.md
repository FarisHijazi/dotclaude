---
name: fsm
description: Deeply study a codebase and produce a finite state machine (FSM) model — enumerating per-component lifecycle states, orthogonal sub-state dimensions (health/mode/breaker/etc.), config gate flags, input classifications, cross-component composite scenarios, and Mermaid diagrams. Use when the user asks to "model states", "draw an FSM", "find all possible states and combinations", "document state transitions", or "map states of components X, Y, Z" — especially for actor-model / distributed / hardware-control systems.
---

# FSM Modeling Skill

Produces a code-grounded, multi-dimensional state model for one or more components, plus Mermaid diagrams. Designed for distributed systems where each component has multiple orthogonal state axes (lifecycle × health × I/O × config gates).

## Output contract

You will produce **two markdown files** in the project's devlog/docs directory (default `docs/devlog/`, follow project's `CLAUDE.md` convention):

1. **`{datetime}-fsm-state-model.md`** — exhaustive state inventory + transitions + composite scenarios + open questions.
2. **`{datetime}-fsm-mermaid-diagrams.md`** — Mermaid diagrams mirroring file 1.

Use `claude_{ISO-datetime}_fsm-...md` if the project uses the GSD devlog naming convention.

---

## Core principles (read before every run)

| Principle | Why |
|---|---|
| **Read full source, don't grep** | State lives in `__init__` field defaults, mutually-flipped flags, dataclasses, `None`-able task refs. Grep misses this. |
| **Over-enumerate then prune** | Surfacing a borderline state lets the user say "drop it." Omitting one means they'll discover the gap during debugging. |
| **Separate orthogonal dimensions** | Most components have ≥2 state axes (lifecycle × health × I/O). Modeling them as one flat list explodes combinatorially and hides structure. |
| **Mark `[GUESS]` honestly** | If the code doesn't *explicitly* enumerate a state or trigger, label it. Better than fabricating confidence. |
| **Mark `(derived)`** | Derived states are computed from multiple fields, not stored. Tag them so the user knows they aren't a flag they can grep for. |
| **Inputs are states** | When a system accepts commands, the *input space* is part of the FSM: `< min`, `= 0`, `in range`, `> max`, `> global_limit`, `negative`, `empty fleet`, `uninitialized`. Each is a branch. |
| **Composite scenarios are the deliverable** | Per-component diagrams are scaffolding. The actual value is in `(fleet × supervisor × miner)` tuples — happy path, failure cascade, structural empty, startup. |

---

## Workflow — 5 phases

### Phase 1 — Scope

**Goal:** confirm what to model.

1. Identify the components from the user's message. If they listed 3 (e.g. "fleet-controller, supervisor, miner"), all 3 are in scope. If unclear, **ask** via `AskUserQuestion` — list candidates pulled from `actors/`, `services/`, top-level Python classes, etc.
2. Identify the **input commands** the user mentioned (e.g. "set_fleet_power"). Each command becomes an input-classification section.
3. Identify the **orthogonal conditions** the user mentioned (e.g. "miners could be asleep / awake", "power_setpoints_enabled True/False", "responding/non-responding", "phase-balanced/not"). These map to sub-state dimensions.

**Output of phase 1:** a 3-line scope statement you write to the conversation (not a file):
```
Components: <list>
Commands to classify: <list>
Orthogonal conditions to model: <list>
```

### Phase 2 — Read

**Goal:** ground every state in code, not guesses.

For each component:

1. `Read` the full source file (use offset/limit for large files; don't skip).
2. `Read` related files: settings/config models, recovery/maintenance helpers, monitors (breaker/sensor), `CLAUDE.md` for project-level facts.
3. Note explicitly:
   - **Init fields** (`__init__`) — every `self.x = ...` is potential state
   - **Dataclass / Pydantic fields** — these are *the* explicit state record
   - **Methods that flip flags** — `start_*`, `stop_*`, `initialize`, `set_*`, `enable_*`
   - **Methods that check flags** — `if self.x:` reveals which states are distinct
   - **`None`-able task refs** — `if self._task is None` is a state distinction
   - **Comments calling out states** — "H4: Failure" style markers
   - **Config gate flags** — `power_setpoints_enabled`, env vars, feature flags

**Checklist before leaving Phase 2:**
- [ ] Read every component's source file completely
- [ ] Read config/settings models
- [ ] Read recovery / maintenance helpers
- [ ] Read project `CLAUDE.md` if present
- [ ] Listed every boolean flag, every `None`-able ref, every enum field per component

### Phase 3 — Model

**Goal:** for each component, draft 5 state-dimension tables.

For each component, produce:

#### 3.1 Lifecycle states (mutually exclusive)
Big-picture "what is this thing doing": `UNINITIALIZED`, `INITIALIZING`, `RUNNING`, `RUNNING_DEGRADED`, `INIT_FAILED`, `STOPPED`, `EMERGENCY_SHUTDOWN`.

Columns: **State | How detected (code condition) | Description**.

#### 3.2 Mode / role sub-states (mutually exclusive within RUNNING)
What mode the component is in: e.g. miner `SLEEPING / AWAKE_AT_SETPOINT / AWAKE_RAMPING / AWAKE_UNDERCLOCKED`.

#### 3.3 Health / responsiveness sub-states (orthogonal)
Is it working: `HEALTHY / TRANSIENTLY_FAILING / UNHEALTHY_TIMEOUT / UNHEALTHY_FAILURES`.

#### 3.4 Subsystem sub-states (orthogonal, when applicable)
For components owning a monitor / driver: `BREAKER_ONLINE / BREAKER_OFFLINE_TRANSIENT / BREAKER_OFFLINE_RECONNECTING`. Or batch processing: `BATCH_IDLE / BATCH_COLLECTING / BATCH_PROCESSING / BATCH_REDISTRIBUTING / BATCH_DELEGATING`.

#### 3.5 Config gate flags (orthogonal, slow-changing)
Booleans from config that radically change behavior: `power_setpoints_enabled`, `ENABLE_POWER_SETPOINT`, `enabled`, feature flags.

Columns: **Flag | Source | Effect**.

#### 3.6 Transitions
ASCII arrows in a fenced block:
```
STATE_FROM --trigger / method / condition--> STATE_TO   [GUESS if not explicit]
```
Group by source state. One arrow per actual code path.

### Phase 4 — Compose

**Goal:** what the user actually debugs against.

Produce composite-scenario tables — realistic cross-component tuples:

| Section | Contents |
|---|---|
| **Happy paths** | Normal commands flowing through fully healthy system |
| **Input classification** | One row per input bucket × system state (this is the user's main ask when commands are involved) |
| **Controllable/observable mixes** | What happens when some components are config-gated off |
| **Failure cascades** | Per-component failure → propagation across components |
| **Subsystem-offline scenarios** | Breaker offline / monitor offline / dependency unreachable |
| **Structural / boundary scenarios** | Empty fleet, zero-controllable, single-phase, etc. |
| **Startup scenarios** | Cold start, restart-preserving-state, set-to-sleep-on-startup combinations |

Each row: **# | Scenario tuple | Trigger | Behavior**.

### Phase 5 — Diagram

**Goal:** Mermaid diagrams in file 2.

For each component:

1. **`stateDiagram-v2`** with nested parallel regions for orthogonal sub-states:
   ```
   state RUNNING {
       [*] --> Health
       [*] --> Subsystem
       state Health { ... }
       state Subsystem { ... }
   }
   ```
2. **`flowchart TD`** for any input-classification decision tree.
3. **`sequenceDiagram`** for important cross-component flows (failure cascades, command dispatch).
4. **2×2 / 3×3 cross-product `stateDiagram-v2`** for the most-debugged combinations (e.g. `SLEEPING/AWAKE × HEALTHY/UNHEALTHY`).
5. **Annotations** — use `note right of X` for `[GUESS]` callouts and policy comments.

Then end **file 1** with an `## Open questions for the user` section (5–8 items) covering:
- Ambiguous derivation thresholds
- Retry/recovery cadences not in code
- Pathological-combination behavior (e.g. "all components failed")
- Whether terminal states can recover
- Runtime vs restart-only config flips
- States to drop if too granular

End **file 2** with no closing prose — diagrams speak for themselves.

---

## Mermaid quick reference

### Parallel regions inside a state
```mermaid
state RUNNING {
    [*] --> Health
    [*] --> Breaker
    state Health { [*] --> HEALTHY; HEALTHY --> UNHEALTHY }
    state Breaker { [*] --> ONLINE; ONLINE --> OFFLINE }
}
```

### Transition with multi-line label
```
A --> B: trigger / method<br/>condition / [GUESS]
```

### Note for [GUESS] caveat
```
note right of STATE
    [GUESS] cadence not in code,
    inferred from comments
end note
```

### Decision-tree flowchart for input classification
```mermaid
flowchart TD
    cmd[Incoming: set_power(P)]
    cmd --> c1{P > global_limit?}
    c1 -->|Yes| REJ[INPUT_ABOVE_LIMIT: return {}]
    c1 -->|No| c2{P == 0?}
    c2 -->|Yes| ZERO[INPUT_ZERO: sleep all]
    c2 -->|No| ...
```

---

## Anti-patterns (avoid)

| ❌ Anti-pattern | ✅ Instead |
|---|---|
| Flat `HEALTHY_SLEEPING_BREAKER_ONLINE` mega-state | Separate parallel regions, show 2×2 in composite |
| Inventing transitions to make the diagram "complete" | Mark `[GUESS]` or omit |
| Skipping the input-classification table | When commands enter the system, this IS the main FSM the user cares about |
| Omitting config gate flags | `enabled=False` is a state — model it |
| Single big diagram for everything | One stateDiagram per component, plus composites |
| Asserting completeness | End with explicit "open questions" — there's always ambiguity |
| Mermaid `state X {...}` with no `[*] -->` inside | Inner states need an initial pseudostate or Mermaid silently breaks |

---

## Done criteria

Before considering the run complete:

- [ ] Phase 1 scope statement printed to conversation
- [ ] All component source files fully read (not just searched)
- [ ] File 1 written with every component covered in the 5 sub-tables of Phase 3
- [ ] At least one input-classification table if commands are in scope
- [ ] Composite scenarios table populated (≥4 sections)
- [ ] File 1 ends with 5–8 open questions
- [ ] File 2 has one `stateDiagram-v2` per component plus ≥1 flowchart and ≥1 sequenceDiagram
- [ ] Every `[GUESS]` is justified by ambiguity in code (not laziness)
- [ ] Closing message to user includes: "I over-enumerated — tell me which states to prune and I'll regenerate."

---

## Notes

- For very large source files (>2000 lines), read in chunks with `offset`/`limit` rather than skipping.
- If the project already has FSM docs (`grep -ri "state machine\|finite state" docs/`), read them first — extend, don't duplicate.
- Match the project's existing devlog naming convention. If it uses `claude_{ISO}_description.md` (GSD style), follow that. Otherwise pick a clear ISO-prefixed name.
- If diagrams get very large, consider splitting one component into two files (`fsm-supervisor.md`, `fsm-supervisor-mermaid.md`) — the user can scroll one diagram per screen.
- Always link file 2 from file 1 and vice versa so the reader can jump.
