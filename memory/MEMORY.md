# Global Memory

## Feedback

- [Log actual values, not hardcoded strings](feedback_logging.md) — use f-strings with `!r`, never hardcode assumed values
- [No defensive getattr on typed models](feedback_no_defensive_getattr.md) — use `obj.field` directly on Pydantic/dataclass
- [Don't delete cloned repos](feedback_dont_delete_repos.md) — never clean up cloned repos without asking
- [Deep data analysis preference](feedback_deep_analysis.md) — user wants exhaustive deep-dive analysis, not surface-level
- [Don't block on questions](feedback_dont_block_on_questions.md) — collect questions in a doc, keep working, don't stop to ask
- [Never touch shared system state](feedback_never_touch_shared_system_state.md) — no iptables/firewall/proxy/DNS changes to fix an app problem; fix root cause
- [Refactoring discipline](feedback_refactoring_discipline.md) — trace ALL downstream refs, grep for old patterns, don't leave half-migrated state
- [Always use uv/uvx for Python](feedback_use_uv_for_python.md) — never pip/pipx, use uv for deps and uvx for CLI tools
- [Robust infra code](feedback_robust_infra_code.md) — never hardcode IDs/IPs, verify installs, handle all states, check real API responses
- [Explicit ownership & workspace pattern](feedback_explicit_ownership_and_workspace.md) — every file has an owner (AI or human), use seed/draft workspace for iterative work, direct write for fire-and-forget
- [Never kill processes by a broad pattern](feedback_never_kill_by_pattern.md) — pkill -f matches the whole command line; read matches, kill by PID
- [Find who already owns it before writing](feedback_find_the_owner_first.md) — grep for ownership language, extend the owner's method, never add a second writer
- [Never render absent data as an answer](feedback_never_render_absent_data.md) — gate UI on a sticky hasLoaded, not on !loading
