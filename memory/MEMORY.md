# Global Memory

`~/.claude/memory/` is the source of truth. `~/.codex/memory/` is a one-way
mirror: edit the Claude source, then run
`uv run --no-project ~/.claude/scripts/sync-codex-memory.py` to sync immediately.
Edits made only to the Codex copy are overwritten.

Infrastructure notes: `ansible-proxmox/memory/MEMORY.md`; the local checkout is listed in `~/.claude/CLAUDE.local.md`.
This is deliberately a plain path, not an `@` include; read it when relevant.

## Feedback

- [No pairing-code sign-in](feedback_no_pairing_codes.md) — use self-hosted identity/Authentik and automatic renewal; do not offer recurring codes or QR pairing as the solution.
- [Never shut down machines](feedback_never_power_off.md) — never shut down, reboot, reset, or power-cycle; generic recovery approval never overrides this rule.

- [Log actual values, not hardcoded strings](feedback_logging.md) — use f-strings with `!r`, never hardcode assumed values
- [Don't delete cloned repos](feedback_dont_delete_repos.md) — never clean up cloned repos without asking
- [Deep data analysis preference](feedback_deep_analysis.md) — user wants exhaustive deep-dive analysis, not surface-level
- [Don't block on questions](feedback_dont_block_on_questions.md) — collect questions in a doc, keep working, don't stop to ask
- [Never touch shared system state](feedback_never_touch_shared_system_state.md) — no iptables/firewall/proxy/DNS changes to fix an app problem; fix root cause
- [Refactoring discipline](feedback_refactoring_discipline.md) — trace ALL downstream refs, grep for old patterns, don't leave half-migrated state
- [Always use uv/uvx for Python](feedback_use_uv_for_python.md) — never pip/pipx, use uv for deps and uvx for CLI tools
- [Explicit ownership & workspace pattern](feedback_explicit_ownership_and_workspace.md) — every file has an owner (AI or human), use seed/draft workspace for iterative work, direct write for fire-and-forget
- [Never kill processes by a broad pattern](feedback_never_kill_by_pattern.md) — pkill -f matches the whole command line; read matches, kill by PID
- [Find who already owns it before writing](feedback_find_the_owner_first.md) — grep for ownership language, extend the owner's method, never add a second writer
- [Never render absent data as an answer](feedback_never_render_absent_data.md) — gate UI on a sticky hasLoaded, not on !loading
- [Monkeypatch imported symbols](feedback_monkeypatch.md) — patch the namespace that consumes the symbol
- [Review changes](feedback_review_changes.md) — exercise affected paths and inspect runtime behavior

## Private preferences

- [Resale ad preferences and history](feedback_resale_ads.local.md) — private local note; excluded from Git
