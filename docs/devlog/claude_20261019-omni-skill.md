# omni skill (2026-10-19)

`skills/omni/SKILL.md` teaches agents to search the user's indexed personal data (Gmail, Drive,
WhatsApp, iMessage, Basecamp + Campfire) with the `omni` CLI from `~/Projects/omni`
(installed with `uv tool install --editable ~/Projects/omni`; that repo owns the CLI and docs).

Tested with skill-creator, 3 real questions (lease rent, a Basecamp work topic, an overdue
invoice); prompts and outputs stay outside this public repo because they hold private data.
- Iteration 1 (subagents in the omni repo): tie, 81% vs 78%, because the repo's CLAUDE.md
  already told the baseline about omni. Both stopped at the literal answer and missed later
  developments, so the skill gained a "sweep for what happened next" rule.
- Iteration 2 (`claude -p` from /tmp, baseline with `--disallowedTools Skill`): the skill
  triggered unprompted on all 3, 100% vs 0% pass. The baseline only had one Gmail account
  via MCP and no Basecamp, and answered "not found" each time. The sweep rule surfaced the
  later card declines on the invoice question.
