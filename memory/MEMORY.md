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
