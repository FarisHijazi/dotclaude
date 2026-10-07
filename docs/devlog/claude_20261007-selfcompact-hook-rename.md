# Rename hooks/auto-compact-continue.sh → hooks/selfcompact.sh (2026-10-07)

Finishes the 2026-10-04 rename (`claude_20261004-selfexit-selfcompact-rename.md`). That one renamed
the user-facing `/selfexit` and `/selfcompact` and left the hook script's name alone. Now the script
matches too.

- `git mv hooks/auto-compact-continue.sh hooks/selfcompact.sh`. References updated in
  `settings.json` (Stop and PostCompact), `README.md`, `commands/selfcompact.md` and
  `scripts/cc-watch-session.sh`. Comments in cc-notify updated too (`LESSONS.md`, `CLAUDE.md`,
  `bin/cc-type-lock.sh`, `hooks/cc-color-apply.sh`).
- **Compat symlink** `hooks/auto-compact-continue.sh -> selfcompact.sh`, NOT tracked. Sessions
  that were already running snapshot their hooks at startup and still call the old path. Delete it
  once every session has restarted.
- Remote boxes carry their own copy under the old name, registered in their own
  settings.json. They are untouched and keep working.
- Tested: `--show` runs through the new path and the symlink, and a Stop payload piped into the
  new path exits 0.
