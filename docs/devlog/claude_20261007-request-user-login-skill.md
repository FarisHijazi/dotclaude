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

## type-password.sh: sudo / ssh prompts through tmux

New `scripts/type-password.sh <pane> <name> [--from keychain|bw]`. Waits up to
20 s for a `password|passphrase|passcode ...:` last line, asks approve.sh, loads
the secret (Keychain service `request-user-login`, or `bw get password`) into a
tmux buffer, pastes it, presses Enter, then checks for "Sorry, try again" /
"Permission denied". Tested with fake bash prompts and throwaway Keychain items:
right secret matched (exit 0), wrong one exit 5, missing exit 6, a plain shell
prompt exit 2 with nothing typed. Gotcha: `capture-pane` returns the blank rows
below the cursor, so strip blank lines before `tail`. Not yet tested on real
sudo/ssh (needs the user's password stored in the Keychain).

- Added `--from stdin` (secret held on fd 3 so approve.sh/tmux don't eat it) for
  passwords the user gives in chat; the user does not want a Keychain step.
  Verified for real on 2026-10-07: `sudo -k; sudo -v` → SUDO-OK, and
  `ssh -o PubkeyAuthentication=no localhost` → logged in, both exit 0.

## Renamed to `/sudo`

The skill is now `skills/sudo/` (was `request-user-login`), its browser script is
`scripts/sudo.sh`, and every path/name followed: the `$TMPDIR/sudo/` grant and
watch-flag dir, the alerter groups, the Keychain service (`sudo`), login-watch,
CLAUDE.md and memory. Older sections above keep the old names. Retested after the
rename: `sudo.sh` usage, real `sudo -v` via `type-password.sh --from stdin`, and the
login-watch hook. A web search found nothing that already does this; the closest is
nextbrowser-oss's `bitwarden-autofill-login` (Chromium autofill only, no terminal
prompts, no approval click).

## login-watch renamed to `/sticky-sudo`

The per-session watcher is now `skills/sticky-sudo/` (`/sticky-sudo on|off|status`; briefly `/sudomode`); the
main skill stays `/sudo`. Hook retested: no flag gives no output, flag gives the reminder.
