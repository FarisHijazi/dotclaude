# sudo

Claude Code skill: logs in for you, never sees the secret.

- **Chrome logins**: one notification click, then Bitwarden autofills (`scripts/sudo.sh`),
  Google SSO, or a Bitwarden passkey (`scripts/confirm-passkey.sh`).
- **Terminal prompts**: sudo / ssh / passphrases in a tmux pane (`scripts/type-password.sh`).
- **Claude in Chrome permission window**: OCR + one notification click, then it clicks
  "Always allow actions on this site" (`scripts/allow_chrome_prompt.py`).
- **Stuck**: `scripts/approve.sh need "<what>"` sends a "Claude needs you" notification.

```text
/sudo                    Claude uses it by itself when it hits a login
/sudo hook [on|off|status]   this session: flag every login wall in Chrome
```

Needs macOS, `alerter`, Hammerspoon (`hs.ipc`, Accessibility), Chrome + Bitwarden, tmux.
Linux X11 uses `xdotool` and `--title` for autofill. Native login buttons also
accept `--window-id ID --click X,Y --via google`, after the caller verifies the
popup in a screenshot. Bitwarden passkey confirmation uses Python 3, `xprop`,
`scrot`, and Tesseract English OCR, without restarting Chrome. See `SKILL.md`
for the target guards and approval behavior.
Run regressions with `python3 skills/sudo/tests/passkey_linux_test.py` from the
repository root.
Every approval is a notification click by default; `YOLO=1`, set by the user only, skips it. Details: `SKILL.md`.
