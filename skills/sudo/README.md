# sudo

Claude Code skill: logs in for you, never sees the secret.

- **Chrome logins**: one notification click, then Bitwarden autofills (`scripts/sudo.sh`),
  Google SSO, or a Bitwarden passkey (`scripts/confirm-passkey.sh`).
- **Terminal prompts**: sudo / ssh / passphrases in a tmux pane (`scripts/type-password.sh`).
- **Stuck**: `scripts/approve.sh need "<what>"` sends a "Claude needs you" notification.

```text
/sudo                    Claude uses it by itself when it hits a login
/sudo hook [on|off|status]   this session: flag every login wall in Chrome
```

Needs macOS, `alerter`, Hammerspoon (`hs.ipc`, Accessibility), Chrome + Bitwarden, tmux.
Linux (X11): `xdotool` instead, and pass `--title` (see `scripts/sudo-linux.sh`).
`YOLO=1` (default in `approve.sh`) skips the click. Details: `SKILL.md`.
