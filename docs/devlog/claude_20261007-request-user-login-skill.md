# request-user-login skill (2026-10-07)

Added `skills/request-user-login/`. It handles login walls in Claude in Chrome
with one click from the user on a macOS notification: Bitwarden fills the
password, Claude clicks through Google SSO, and a Bitwarden passkey is pressed
after its own fresh click. `settings.json` gains `mcp__claude-in-chrome` in
`permissions.allow` and a PostToolUse login-wall hook. `CLAUDE.md` points to
the skill. The full history and gotchas are in the dotfiles repo at
`docs/devlog/claude_20261005-request-user-login-skill.md`.

- 2026-10-07: hook is now opt-in per session via `/login-watch on|off|status` (flag in `$TMPDIR/request-user-login/watch-<session>`, checked by the settings.json hook command; hook script unchanged).

## Hook moved into the login-watch skill (cachebeat pattern)

The PostToolUse hook no longer lives in `settings.json`. It is in
`skills/login-watch/SKILL.md` frontmatter (`hooks:`), which Claude Code registers
only when that skill loads, the way github.com/ARahim3/cachebeat does it. Sessions
that never run `/login-watch` don't run the hook at all. `off` still deletes the
flag file, because a loaded skill's hook stays for the rest of the session.
Tested with fake input: no flag gives no output, flag gives the reminder.

## Shortcut is ⌃⇧L in Default, ⌘⇧L elsewhere; focus is required

- Read from `Preferences` → `extensions.commands`: the `Default` profile binds
  Bitwarden `autofill_login` to `mac:Ctrl+Shift+L`; the dema and thmanyah profiles
  use `Command+Shift+L`. ⌘⇧L and ⌘⇧B both did nothing on Default; ⌃⇧L filled and
  logged in to the router (index.asp) on 2026-10-07.
- Script default changed to `cmd+shift+l` (user approved the script edit).
- Background test: Hammerspoon `event:post(chromeApp)` with Ghostty in front, ⌃⇧L
  → fields stayed empty. Extension shortcuts need Chrome frontmost, so the short
  focus stays.
