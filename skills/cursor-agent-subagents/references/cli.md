# cursor-agent CLI notes

Prefer live `cursor-agent --help` / `cursor-agent models` when anything here
looks stale — the CLI updates itself and flags/models drift.

## Headless invocation

```bash
cursor-agent -p --output-format text|json|stream-json [flags] "prompt…"
```

| Flag | Notes |
| --- | --- |
| `-p` / `--print` | Non-interactive; all tools incl. write + shell available |
| `--output-format` | Only works with `-p`. `text` = final answer only; `json` = one result object; `stream-json` = NDJSON event stream |
| `--stream-partial-output` | With `stream-json`: per-delta assistant text events |
| `--mode ask\|plan` | Read-only modes (`--plan` = shorthand) |
| `--model <id>` | From `cursor-agent models`; bracket overrides exist, e.g. `'claude-opus-4-8[context=1m,effort=high]'` |
| `--trust` | Skip workspace-trust prompt — required headless |
| `-f` / `--force` / `--yolo` | Auto-allow shell commands — required for headless gates/writes |
| `--auto-review` | Server classifier auto-runs safe calls, prompts for rest (interactive-oriented; headless prefers `-f`) |
| `--sandbox enabled\|disabled` | Override sandbox |
| `--approve-mcps` | Auto-approve MCP servers from `mcp.json` |
| `--workspace <path>` | Repo root (defaults to cwd) |
| `--add-dir <path>` | Extra root (repeatable) |
| `-w` / `--worktree [name]` | Isolated worktree at `~/.cursor/worktrees/<repo>/<name>`; name auto-generated if omitted |
| `--worktree-base <ref>` | Base ref for the new worktree (default: current HEAD) |
| `--resume <chatId>` | Continue a session by id, full memory retained |
| `--continue` | Continue most recent session (ambiguous under parallelism — prefer `--resume <id>`) |
| `models` | List live model IDs |
| `status` / `login` | Auth check / interactive login |

## Auth

- Interactive: `cursor-agent login`
- Headless/CI: `CURSOR_API_KEY` env var

## Output schemas (observed 2026-08)

`--output-format json` — single object on stdout:

```json
{"type":"result","subtype":"success","is_error":false,"duration_ms":46581,
 "result":"…final answer…","session_id":"<uuid>","request_id":"<uuid>",
 "usage":{"inputTokens":11849,"outputTokens":370,"cacheReadTokens":41011,"cacheWriteTokens":0}}
```

`--output-format stream-json` — NDJSON, every event has `session_id`:

| Event `type` | Content |
| --- | --- |
| `system` (`subtype:init`) | cwd, model, permissionMode, **session_id** — first line |
| `user` | the prompt echoed back |
| `thinking` (`delta`/`completed`) | reasoning text deltas |
| `assistant` | assistant message text |
| `tool_call` (`started`/`completed`) | tool name + args (globToolCall, read, write, shell, …) |
| `result` | same shape as json format — last line |

Useful one-liners:

```bash
grep -m1 '"subtype":"init"' run.log | jq -r .session_id   # session id
tail -1 run.log | jq '{subtype,is_error,duration_ms}'     # outcome
grep '"subtype":"started"' run.log \
  | jq -r '.tool_call | [keys[] | select(endswith("ToolCall"))][0]' \
  | sort | uniq -c                                        # actions taken, by tool
```

With `--worktree`, a plain-text `Using worktree: <path>` line precedes the JSON
stream (useful: it's the diff location) — don't assume line 1 is JSON.

## Failure signals (observed live, 2026-08)

| Case | Exit | stdout | stderr |
| --- | --- | --- | --- |
| Success | 0 | `result` event, `is_error:false` | — |
| Task failed | 0 | `result` event, `is_error:true` | — |
| Needs clarification | 0 | `result` contains `NEED_HELP:` (brief contract) | — |
| Out of credits (per model family) | 1 | *empty* | `ActionRequiredError: You've hit your usage limit …` |
| Unknown model | 1 | *empty* | `Cannot use this model: … Available models: …` |
| Killed / crashed | ≠0 or none | log ends without `result` event | varies |
| Stalled | n/a (alive) | log mtime stops advancing (normally events stream continuously) | — |

Exit code 0 does NOT mean task success — classify from the `result` event.
Approval prompts and clarifying questions never block headless `-p` runs
(verified: even network+write shell commands ran without `-f`; questions come
out as text) — hang risk is limited to TUI subcommands and missing `--trust`.

## Pitfalls (each one cost real debugging time)

1. **`cursor-agent ls` and bare `resume` are raw-mode TUIs** — they crash/hang
   headless ("Raw mode is not supported"). Never call them from scripts. Track
   session ids yourself from json output.
2. Parallel **writers** on one cwd collide → unique `--worktree` names each.
3. Headless without `--trust` stalls on the trust prompt.
4. Headless write without `-f` proposes but can't apply/run approval-gated
   commands.
5. Model IDs churn (e.g. `composer-2.5-fast` existed once, then didn't).
   Always read `cursor-agent models` in-session before picking.
6. Subagent has no parent-chat memory — constraints live in the brief only.
7. The CLI loads `.cursor/rules`, `AGENTS.md`, `CLAUDE.md`, and MCP servers
   from `mcp.json` — repo context you get for free (and a reason behavior may
   differ between repos).
8. Headless runs exit 0 even when `is_error` might be more nuanced — judge
   success from the `result` event and the actual diff/gates, not the exit
   code alone.
