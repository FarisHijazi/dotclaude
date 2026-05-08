---
name: Refactoring discipline — think holistically, don't leave loose ends
description: When refactoring or restructuring, trace ALL downstream effects proactively. Don't wait for user to catch orphaned references, hardcoded values, or half-migrated state.
type: feedback
---

When Faris asks to refactor, restructure, or clean up — he expects the FULL job done in one pass. He shouldn't have to point out each leftover.

## Mistakes to never repeat

1. **Hardcoded values surviving a refactor.** E.g. moved config to `.env` but left `~/.ssh/id_rsa.pub` hardcoded in a playbook. Should have grepped for all SSH key references across the repo BEFORE claiming done.

2. **Half-applied defaults.** Added a fallback chain (`SSH_KEY_GUEST` → `SSH_KEY`) but also kept a hardcoded `default('~/.ssh/id_ed25519.pub')` — contradicting the entire design. If the design is "everything flows from .env", nothing should have a hardcoded escape hatch.

3. **Not tracing downstream when upstream changed.** Changed output filename from `inventory.auto.ini` → `inventory.ini` but didn't immediately update gitignore, CLAUDE.md, README, and all references. Faris had to ask for each.

4. **Not noticing adjacent concerns.** A misplaced folder sitting at repo root during a "clean up the structure" conversation — should have flagged it proactively.

## How to think next time

**Before starting:** `grep -r` for every value/path/name being changed. Map all references.

**During:** When changing X, ask "what else references X?" For every file touched, ask "what references THIS file?"

**Before claiming done:**
- grep for the OLD pattern (should be gone everywhere)
- grep for hardcoded values that contradict the new design
- scan repo root for files that look misplaced given the new structure
- re-read final state of ALL changed files for internal consistency

**Examples:**
- "Move .env to environments/" → also update .gitignore, README, CLAUDE.md, ansible.cfg, scripts, delete old files
- "Make SSH key configurable" → grep ENTIRE repo for hardcoded key paths
- "Remove .auto. substring" → update every file that mentions "auto"

**Why:** Faris works across multiple jobs and repos. He can't babysit every edit. A refactor that leaves orphaned references is worse than not refactoring — it creates confusion about which pattern is canonical.

**How to apply:** Treat every refactor as a repo-wide grep+fix operation, not a single-file edit. Verify completeness before reporting done.
