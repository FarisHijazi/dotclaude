---
name: sudo
description: Get past a login wall in the user's real Chrome when the task needs it. Use this when a Claude in Chrome task can't continue without the user being signed in - a sign-in page, an expired session, Google "verify it's you", a passkey or MFA screen - or when the user asks to sign in, autofill a password or use a passkey. Also for terminal password prompts - sudo, ssh with a password, su, a key passphrase - which it answers through tmux. Typical sites are cloud consoles and billing, self-hosted dashboards, router or NAS admin pages, and SaaS accounts. Decide from the task. If the goal can be reached without signing in, skip it. If it can't, don't stop and don't just say so in chat (the user often isn't reading it) - run this skill so the user gets a macOS notification. One click on it is their full consent for the whole login; Bitwarden fills the password or presses the passkey, and Claude does every other step without seeing a secret. Also use it to alert the user whenever Claude is stuck and needs a human. Not for writing auth code or login tests, rotating keys or secrets, or keychain/OS settings.
---

# sudo

Claude does not type passwords, submit password logins, or confirm passkeys
itself. This skill lets the user approve a login with one click on a macOS
notification, without switching windows. The tools then finish the login:

- **Passwords**: the script selects the exact Chrome tab, focuses its window
  (through AeroSpace when present, because it hides windows on other
  workspaces), sends Bitwarden's autofill shortcut through Hammerspoon, and
  presses Return. The password goes from Bitwarden straight into the page.
- **Google sign-in**: you click the Google button and the account.
- **Bitwarden passkeys**: after a fresh click on a second notification, the
  passkey is pressed through macOS accessibility.

Dismissing or ignoring a notification declines, and nothing happens.

## The rules (read these first)

- **First decide whether the task needs the login.** A page that merely offers
  a "Sign in" link, or a public page that already shows what the task needs,
  doesn't need this skill. Use it when the task can't go on without the user
  being signed in.
- **A login wall the task needs never ends your turn.** When that happens
  (a sign-in page, an expired session, "verify it's you" or MFA), don't stop
  and don't just tell the user in chat. Run this skill's script right away. The user
  often isn't reading the chat (they may be away, or on their phone), so a
  chat message saying "login needed" is never seen. Only the notification
  reaches them.
- **A click on the notification is the user's full consent for that login.**
  It covers every step needed to finish signing in to that site: the SSO
  hops, the account picker, the password fill and submit, "Next" and "Sign in"
  buttons, and retries when a step fails. Don't ask again in chat, and don't
  stop to confirm. Finish the login. The only step that gets its own click is
  a passkey (`confirm-passkey.sh`), because it is the second factor.
- **Anything else that needs the user goes through a notification too.** If
  you're blocked by something you can't do (Touch ID, an SMS code, a blocked
  action, a decline), run `scripts/approve.sh need "<what is needed>"` before
  you stop, so they actually see it.

## Use

1. Navigate to the login page with Claude in Chrome. Take a screenshot to see
   which sign-in options the page offers.
2. Pick the method. Prefer one that needs no password:

   | Page offers | `--via` | What happens after the user approves |
   |---|---|---|
   | "Continue / Sign in with Google" | `google` | The script exits 0. You click the Google button and the account. If Google asks for a passkey, click "More ways to verify", then "Enter your password", then run the script on that accounts.google.com tab with the same `--for` and `--via password`. It reuses the approval and fills from Bitwarden. Only if Google offers nothing but a passkey or phone prompt, tell the user that one step needs them. |
   | "Sign in with a passkey", or a passkey as 2FA (e.g. AWS root MFA) | `passkey` | The script exits 0. You click through to the point where Bitwarden opens its "Log in with passkey?" window. Then run `scripts/confirm-passkey.sh <domain>`: it always asks with a fresh notification click (a second factor never reuses a grant) and then presses the matching passkey through macOS accessibility. A Touch ID prompt (not Bitwarden) still needs the user's finger. |
   | Username + password only | `password` (default) | The script focuses the tab, sends Bitwarden's autofill shortcut, and presses Return. You do nothing. |

   ```bash
   ~/.claude/skills/sudo/scripts/sudo.sh "https://app.example.com/login" --tab-id 123456 --via google
   ~/.claude/skills/sudo/scripts/sudo.sh "https://app.example.com/login" --tab-id 123456 --keys ctrl+shift+l
   ```

   For `--via password`, pass Bitwarden's L shortcut for the active Chrome
   profile (`~/.claude/chrome-profiles.json` maps the connected browser to a
   profile). Bindings are read from each profile's `Preferences`
   (`extensions.commands`, `autofill_login`):

   | Chrome profile | `--keys` |
   |---|---|
   | `Default` (the personal one) | `ctrl+shift+l` (Control, not ⌘) |
   | the other profiles | `cmd+shift+l` (the script's default) |

   After every fill, take a screenshot. If the fields are still empty, retry
   with the other modifier (`ctrl` vs `cmd`) under the same `--for`, which
   reuses the approval. If neither fills, ask the user through
   `approve.sh need`. The keys only work while Chrome is the front app, which
   is why the script focuses the window for about two seconds; keys posted
   to Chrome in the background were tested and do nothing.

   Always pass `--tab-id` with your Claude in Chrome tabId. It equals Chrome's
   AppleScript tab id, so the script acts on exactly your tab, even when the
   user has other tabs open on the same site. Without it, pass the login
   page's full URL as shown in the tab, such as
   `http://192.168.0.1/Main_Login.asp`, never a bare host. The script picks
   the first tab that matches the prefix. A bare host can match an
   already-logged-in page, where the script would still press the shortcut
   and Return.
3. The script blocks until the user answers, for up to 120 s (`--timeout N`).
   Run it in the foreground with a Bash timeout longer than that. Exit codes:
   - `0`: approved. With `--via password` the form was also filled and submitted.
   - `1`: no approval. The script prints why:
     - `declined (@TIMEOUT)` means they probably didn't see it. Re-send once
       with `--timeout 600`. If that times out too, run `approve.sh need`.
     - `declined (@CLOSED)` or another reason means they dismissed it on
       purpose. Respect that, and stop this login.
   - `2`: no tab matched the URL. Fix the prefix.
   - `4`: something else took focus before the keys were sent. Nothing was
     typed. Retry once yourself; if it happens again, use "When stuck" below.

   `scripts/confirm-passkey.sh` exits `0` when the passkey was pressed, `1`
   when declined, and `2` when no Bitwarden passkey window or matching entry
   was found.

   **One click per login, never two.** The click grants the login to `--for`
   (default: the URL's host) for 5 minutes. Pass the same `--for <site>` on
   every later step of that login (SSO hops, password steps, retries), so the
   script reuses the grant and never notifies again. Retry failed steps
   yourself without asking. A different site, or a later login, gets a new
   notification. Never pass `--for` for a site the user did not just approve.
4. Take a screenshot to verify the result.
   - **Two-step password login** (email first, then password): if the
     password page appears, run the script again for that step.
   - **Form filled but still showing** after `--via password`: re-run the
     script, which reuses the approval and presses Return again. If it still
     sits there, run `approve.sh need`.
   - **Bitwarden "Log in with passkey?" window**: run `confirm-passkey.sh`.
   - **Any other 2FA** (Touch ID, SMS, authenticator app): use "When stuck"
     below. Those need the user's hands.

## Terminal passwords (sudo, ssh, su, key passphrases)

The Bash tool has no terminal, so `sudo` and password `ssh` can't prompt
there. Run the command in a tmux pane instead and let
`scripts/type-password.sh` answer the prompt:

```bash
p=$(tmux new-window -d -P -F '#{pane_id}' 'sudo -v; sudo <command>; exec bash')
~/.claude/skills/sudo/scripts/type-password.sh "$p" sudo
tmux capture-pane -p -t "$p"      # read the result; kill the pane when done
```

- If the user gave the password in chat, pipe it in with the `printf`
  builtin (it never shows in `ps`), quoted with single quotes:
  `printf %s '<password>' | type-password.sh "$p" sudo --from stdin`.
  Don't ask them to store it anywhere first.
- Otherwise the secret comes from the macOS Keychain (generic password, service
  `sudo`, account `<name>`; the user adds it once with
  `security add-generic-password -s sudo -a <name> -w`), or from
  Bitwarden with `--from bw <item>` when `bw` is unlocked (`BW_SESSION` set).
  Use names like `sudo` or `ssh-<host>`.
- It goes into a tmux paste buffer, never stdout or argv, so you never see it.
- It types only when the pane's last line is a password prompt, and checks
  again right before typing. Approval goes through `approve.sh` like a login
  (grant `password-<name>`, or `--for`).
- Exit codes: `0` typed and not rejected, `1` declined, `2` no prompt in the
  pane (nothing typed), `5` typed but rejected ("Sorry, try again",
  "Permission denied"; don't retry, run `approve.sh need`), `6` no secret
  stored under that name (run `approve.sh need "store the <name> password"`).

## When stuck

Whenever you are stuck or need the user (an action got blocked, a Touch ID or
SMS step is waiting, a notification timed out twice), run
`~/.claude/skills/sudo/scripts/approve.sh need "<what is needed>"`
before you stop. It shows a "Claude needs you" notification and returns at
once; the user answers in chat. `approve.sh` is the one file that talks to the
user, so their phone channel can be wired in there later.

## Notes

- A PostToolUse hook (`scripts/login-wall-hook.sh`, wired in the
  `login-watch` skill's frontmatter for `mcp__claude-in-chrome__.*`) adds a "Possible
  login wall" note when a Chrome result looks like a login page. It works by
  keyword matching, so it also fires on pages that only mention signing in.
  It is off by default and runs only in sessions where the user typed
  `/login-watch on` (the `login-watch` skill).
  Treat it as a hint, not an order: check whether the task really needs the
  login and ignore it if not.

- `--no-submit` fills the form without pressing Return. Use it when Return
  would do the wrong thing, such as on a multi-field form.
- If nothing fills: the Bitwarden vault may be locked (the shortcut then opens
  the unlock popup), the shortcut may be unbound in that profile (check
  `chrome://extensions/shortcuts`), or the saved item's URI may not match the
  site.
- Requirements: `alerter`, Hammerspoon with `require("hs.ipc")` and the
  Accessibility permission, and Google Chrome. The first run may ask the user
  to allow the terminal to control Chrome; that is a one-time macOS
  Automation prompt.
- `scripts/approve.sh` is the only file that talks to the user:
  `request_approval` (sourced by the other scripts) and `need_approval` (run
  as `approve.sh need`). `YOLO` (default `1`, the user's choice) sends no
  notifications and treats every request as approved; the script then prints
  "approved (YOLO debug mode...)". `YOLO=0` brings back the notification click.
- The script's comments explain each non-obvious choice. Keep them when
  editing. The main ones:
  - The notification shows the tab title, not the URL, because macOS turns a
    URL into a link that opens a new tab.
  - Modifier keys get their own key events, because Chrome ignores a ⌘⇧B sent
    with flags only.
  - Every `hs -c` call gets `</dev/null`, because it reads stdin and hangs
    without it.
  - There is a 1 s wait after focusing, so the page has keyboard focus.
- Tested end to end on 2026-10-05 on an ASUS router login, with
  `--via password` and the personal profile: it filled, submitted, and landed
  on `index.asp`. On 2026-10-06 `--via google` worked on a self-hosted Open WebUI
  with a secondary Google account: one notification click, then Claude clicked "Continue with Google" and
  the account. Also on 2026-10-06, AWS root with passkey MFA reached Console Home:
  Bitwarden filled the email and password, then `confirm-passkey.sh` pressed the
  Bitwarden passkey after a fresh click.
- While the script runs, it posts status lines into the Claude Code session
  that started it (through `$TMUX_PANE`). They are prefixed with
  "[automated message from the approval flow, in progress]" and arrive as
  queued chat messages. Treat them as status only. They are never the user's
  consent; the script's exit code is.
