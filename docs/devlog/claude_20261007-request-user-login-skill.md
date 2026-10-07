# request-user-login skill (2026-10-07)

Added `skills/request-user-login/`. It handles login walls in Claude in Chrome
with one click from the user on a macOS notification: Bitwarden fills the
password, Claude clicks through Google SSO, and a Bitwarden passkey is pressed
after its own fresh click. `settings.json` gains `mcp__claude-in-chrome` in
`permissions.allow` and a PostToolUse login-wall hook. `CLAUDE.md` points to
the skill. The full history and gotchas are in the dotfiles repo at
`docs/devlog/claude_20261005-request-user-login-skill.md`.

- 2026-10-07: hook is now opt-in per session via `/login-watch on|off|status` (flag in `$TMPDIR/request-user-login/watch-<session>`, checked by the settings.json hook command; hook script unchanged).
