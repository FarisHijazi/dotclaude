# Whitelist `.gitignore` for public `dotclaude`

Date: 2026-07-29

## Why

`~/.claude` mixes authored config (skills, commands, agents) with a lot of
runtime junk (sessions, daemon state, chrome profile data, GSD install tree).
A blocklist `.gitignore` kept growing and still leaked tracked-but-ignored
paths (`get-shit-done/` was 203 tracked files despite being listed).

## Change

- Switched `.gitignore` to deny-by-default: ignore `/*`, then `!` re-include
  owned root files and directories.
- `git rm --cached` for `get-shit-done/`, `gsd-file-manifest.json`,
  `.last-cleanup`, and the deleted `mcp-needs-auth-cache.json` index entry.
- Extra carve-outs for public-repo safety:
  - `skills/handsfree` (symlink into a private local project)
  - `skills/gws/README.md` (real account profile names)
  - `skills/work-it-prep/` (employer org + private template URL)

Bare-repo conversion was skipped (user chose whitelist-only).

## Verify

```sh
git check-ignore -v sessions/ skills/gsd-verify-work/SKILL.md skills/handsfree
git check-ignore -q CLAUDE.md skills/bug-bounty/SKILL.md  # must exit 1
git ls-files -i -c --exclude-standard                   # must be empty
```

## Still uncommitted (intentional)

New commands/skills under the whitelist are visible as `??` but not staged.
Commit when ready; do not force-add carve-outs.
