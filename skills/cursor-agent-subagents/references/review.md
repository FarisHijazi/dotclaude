# Review and land

Treat the subagent report as claims. Reality is the tree + gates you re-run.

1. `git status` / `git diff` (and untracked `??`). If `--worktree <name>` was set, inspect in `~/.cursor/worktrees/<repo>/<name>`.
2. Reject scope outside the brief allow-list.
3. Treat unbriefed test edits, skips, and loosened assertions as failures until justified.
4. Re-run the same gate commands from the brief.
5. **You** commit or merge — never the subagent.

## Rework

```bash
cursor-agent -p --resume <session_id> --output-format json --trust -f \
  "Delta only: what is wrong; what must still pass."
```

(`session_id` comes from the original run's json/stream-json output — first
line's `system:init` event or the final `result` object.)

## Parallel merge

Review each worktree alone, then integrate in dependency order and re-run gates on the combined tree.
