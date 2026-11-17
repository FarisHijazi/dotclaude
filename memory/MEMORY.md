# Global Memory

Edit shared memories in `~/.claude/memory/`; `~/.codex/memory/` is its one-way mirror.
Run `uv run --no-project ~/.claude/scripts/sync-codex-memory.py` to sync immediately.

Infrastructure notes: `ansible-proxmox/memory/MEMORY.md`; the local checkout is in
`~/.claude/CLAUDE.local.md`. Paths are deliberately plain, not `@` includes.

## Preferences

- Continue independent work while awaiting clarification; pause only work that requires the answer.
- Keep cloned repositories for reference unless the user explicitly requests cleanup.
- Use `uv` for Python projects/dependencies and `uvx` for tools; never `pip` or `pipx`.
- Keep user-owned `seed.md`, `TODO.todo` and `personalnotes/` unchanged unless explicitly asked to edit them.
- Use a user-owned seed and AI-owned draft for genuinely iterative artifacts; write simple outputs directly.

## Read when relevant

- [Process and cleanup safety](feedback_never_kill_by_pattern.md)
- [Power-state restrictions](feedback_never_power_off.md)
- [Shared-system boundaries](feedback_never_touch_shared_system_state.md)
- [Find the existing owner](feedback_find_the_owner_first.md)
- [Unloaded and unavailable data](feedback_never_render_absent_data.md)
- [No pairing-code sign-in](feedback_no_pairing_codes.md)
- [Private resale preferences](feedback_resale_ads.local.md) — local only; excluded from Git
