---
name: chrome-identify
description: Identify every connected Chrome profile (deviceId ↔ Google account) and save the mapping
allowed-tools: ToolSearch, AskUserQuestion, Write, Read, mcp__claude-in-chrome__list_connected_browsers, mcp__claude-in-chrome__select_browser, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__get_page_text
---

# /chrome-identify

Map each Chrome browser connected to the `claude-in-chrome` extension to its
signed-in Google account, and persist the result to `~/.claude/chrome-profiles.json`.

**Why:** the extension's `deviceId` is **stable across reboots/restarts** (it
only changes on extension reinstall, profile recreation, or storage clear), but
the `"Browser N"` display names are **connection-order and NOT stable**. So
the durable key is `deviceId`, and the reliable way to know *which profile* a
deviceId is, is to open `myaccount.google.com` in it and read the account.

## Steps

1. **Load the browser tools** (if deferred) in one call:
   `ToolSearch "select:mcp__claude-in-chrome__list_connected_browsers,mcp__claude-in-chrome__select_browser,mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__get_page_text"`

2. **List connected browsers:** call `list_connected_browsers`. Record every
   `deviceId` + display `name`.

3. **Completeness check (ask the user).** The extension only sees Chrome windows
   that are **launched AND have the Claude extension enabled/connected**. Read
   `~/.claude/chrome-profiles.json` if it exists to learn how many profiles are
   expected. Then ask the user with `AskUserQuestion`:
   *"I see N connected Chrome browser(s). Are all the profiles you want to identify
   currently open with the Claude extension connected?"* — options: **Yes, all open**
   / **No — let me launch the missing one(s)**. If they need to launch more, wait,
   then re-run `list_connected_browsers`. Do not assume a fixed count; confirm.

4. **Probe each connected browser** (iterate every `deviceId` from step 2 —
   this command *intends* to visit all of them, so probe each in turn rather than
   asking the user to pick just one):
   - `select_browser(deviceId)`
   - `tabs_context_mcp(createIfEmpty: true)` → take a `tabId`
   - `navigate(tabId, "https://myaccount.google.com/")`
   - `get_page_text(tabId)` → read the **display name + email** (the page shows
     e.g. `Jane Doe` / `user@example.com`). If it redirects to a login page,
     that profile is signed out — record `email: null, signed_in: false`.

5. **Name each profile.** Match the email to the user's known accounts (see
   `~/.claude/CLAUDE.local.md`, if present) and reuse the user's existing short
   profile names (e.g. `work` / `personal` / `client-a`). If an email doesn't
   match any known account, keep the email and ask the user what short name to use.

6. **Write `~/.claude/chrome-profiles.json`** (merge with any existing file; key on
   `deviceId`). Schema:
   ```json
   {
     "_note": "deviceId ↔ Chrome profile. deviceId is stable across reboots; 'Browser N' names are not — key on deviceId. Re-run /chrome-identify if a deviceId stops matching.",
     "profiles": [
       { "deviceId": "…", "name": "work", "email": "user@example.com", "confirmed": true }
     ]
   }
   ```

7. **Report** a table to the user: `deviceId | display name | email | profile name`,
   and note any profile that was signed out or unconfirmed.

## Notes
- Only probe the user's own profiles, at their request (reading the signed-in
  Google email). Never enter credentials or log in — if a profile is signed out,
  report it and let the user sign in.
- Downstream callers pick the profile by matching the working directory: see the
  "for using /chrome" rules in `~/.claude/CLAUDE.local.md`.
