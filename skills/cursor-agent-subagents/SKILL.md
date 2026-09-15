---
name: cursor-agent-subagents
description: >-
  Offload self-contained, clearly-scoped, finishable tasks to headless Cursor
  Agent CLI (`cursor-agent`) subagents instead of native Claude subagents —
  Cursor usage is cheap/free for the user. Fire-and-forget dispatch with a
  bundled monitor that detects done / failed / crashed / stuck / out-of-credits
  / needs-clarification. Use whenever the user wants parallel Cursor workers,
  "delegate to Cursor", "spin off cursor agents", worktree-isolated
  implementers, a second opinion from a non-Claude model, or to continue a
  previous cursor-agent run. Skip for tiny inline edits and for vague tasks
  that need back-and-forth (do those yourself).
compatibility: Requires cursor-agent on PATH, auth (`cursor-agent login` / CURSOR_API_KEY), jq.
---

# cursor-agent-subagents

You are the **orchestrator**. Dispatch headless `cursor-agent` subagents for
**self-contained tasks** (clear goal, clear done-condition, everything needed
in the brief or repo), let them run to completion in the background, poll their
state, and handle the outcome. They see only the prompt + workspace — not this
chat. You verify and commit.

Why this exists: these tasks would otherwise burn Claude subagent tokens;
Cursor runs them at no marginal cost. Headless `-p` mode **never blocks on
stdin** — no approval prompt or clarifying question can hang a run (verified) —
so fire-and-forget is safe. Never run TUI subcommands (`ls`, bare `resume`)
from scripts; they need raw stdin and hang.

## Setup (once per session)

```bash
cursor-agent status   # logged in?
cursor-agent models   # live model IDs — they drift; NEVER hardcode or invent
```

## Dispatch and monitor: scripts/cagent.sh

The bundled script owns the lifecycle (background dispatch, log capture, state
classification). One run = one name.

```bash
CA=~/.claude/skills/cursor-agent-subagents/scripts/cagent.sh

# Dispatch (from the repo root; MODEL optional — defaults to cursor-grok-4.5-high)
WORKTREE=fix-refund $CA run fix-refund "$(cat BRIEF.md)"
MODE=ask $CA run audit "…read-only brief…"
MODEL=gpt-5.3-codex-high $CA run hard-bug "…brief…"   # override per run

$CA statusall          # every run: NAME STATE detail
$CA status fix-refund  # one run
$CA result fix-refund  # final report text
$CA sid fix-refund     # session_id for --resume
```

Runs persist under `$CAGENT_RUNS` (default `~/.cache/cagent-runs`). Poll with
`statusall` every few minutes (or `sleep`+check in background); don't busy-wait.

## States and what YOU do about each

| State | Meaning | Your move |
| --- | --- | --- |
| `RUNNING` | events still streaming | wait |
| `DONE` | result event, no error | verify diff + gates, then land ([references/review.md](references/review.md)) |
| `NEED_HELP` | agent emitted `NEED_HELP:` line | answer it: `cursor-agent -p --resume $($CA sid <name>) --trust -f "<answer + what must still pass>"` — full memory retained. If only the user can answer, surface the question to them |
| `FAILED` | result with `is_error:true` | read `result <name>`, fix brief or approach, resume or redispatch |
| `OUT_OF_CREDITS` | stderr "hit your usage limit" | limits are per model family — retry the same brief on a different family (e.g. fable exhausted while composer fine). Tell the user which family is out |
| `BAD_MODEL` | model ID doesn't exist | re-read `cursor-agent models`, redispatch |
| `CRASHED` | process died, no result event | check `<run>/err`, redispatch; consider resuming the sid if the log shows partial progress |
| `STALLED` | alive but no log activity > `CAGENT_STALL_SECS` (default 300) | kill the pid, then resume the sid with "continue; you stalled" or redispatch |

## The brief contract (every dispatch)

Follow [references/brief-template.md](references/brief-template.md). Non-negotiables:

1. **Self-contained** — no chat memory; a constraint not in the brief or repo
   does not exist for the agent.
2. **Escape hatch, always** — include verbatim: *"If anything is unclear, or
   you are blocked, or a required resource is missing: output a single line
   starting with `NEED_HELP:` followed by your question, and stop."* This is
   what makes NEED_HELP detection work; without it agents guess or ask
   questions into the void (exit 0 either way — never trust exit codes alone).
3. **Real gate commands** to run before finishing; **do NOT commit**.
4. **Report format**: what changed, files touched, gate outcomes.

## Parallelism and isolation

- Dispatch the whole fleet in one turn; each run gets a unique name.
- **Writers**: unique `WORKTREE=<name>` each — diff lands in
  `~/.cursor/worktrees/<repo>/<name>` (also printed as the log's first line).
  Never two writers on one working tree. Give each an explicit file allow-list.
- **Ask/plan** agents: same cwd fine.

## Model picks

From live `cursor-agent models` only. **Default: `cursor-grok-4.5-high`**
(currently free-promo — the user wants it as the workhorse; cagent.sh already
defaults to it). Heuristics for overrides: `composer-*` for fast routine
explore; `*-high`/`*-xhigh` gpt/codex/opus for hard reasoning; a non-Claude
family when the point is a second opinion. On OUT_OF_CREDITS, switching family
is usually enough. If the promo ends and grok starts returning
OUT_OF_CREDITS, fall back to `composer-2.5` / `auto` and tell the user.

## Raw one-shots (no monitor needed)

For a quick question where you'll wait synchronously:

```bash
out=$(cursor-agent -p --output-format json --mode ask --trust \
      --model <id> --workspace "$PWD" "…brief…")
echo "$out" | jq -r .result        # answer
echo "$out" | jq -r .session_id    # keep if follow-up likely
```

Flag details, output schemas, jq one-liners, pitfalls:
[references/cli.md](references/cli.md).

## After DONE

Treat the report as claims: inspect the worktree diff, re-run gates yourself,
reject out-of-scope edits, **you** commit/merge —
[references/review.md](references/review.md).
