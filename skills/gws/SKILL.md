---
name: gws
description: Run the Google Workspace CLI (`gws`) against multiple Google accounts by pointing `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` at a per-account profile directory under `~/.config/gws/profiles/<name>/`. Use when asked to query Gmail/Drive/Calendar/Sheets/etc from a specific account, list/set up gws profiles, or sign a new Google account into gws.
---

# gws multi-account usage

`gws` (Google Workspace CLI, typically at `/opt/homebrew/bin/gws`) stores
credentials in a single config directory. To support multiple accounts we keep
**one isolated config dir per account** and select it with the **native**
environment variable `GOOGLE_WORKSPACE_CLI_CONFIG_DIR`. No wrapper, no aliases.

```
~/.config/gws/profiles/
  default/        <- original creds copied here when migrating
  <profile-1>/    <- e.g. personal
  <profile-2>/    <- e.g. work
  <profile-3>/    <- e.g. side-org
```

Each profile directory contains:
- `client_secret.json` - the OAuth **app** identity (shared GCP project / OAuth
  client). The same `client_secret.json` can be reused across all profiles -
  it identifies the *app*, not the *user*.
- `credentials.enc` + `token_cache.json` - the per-user tokens, written by
  `gws auth login`. These are per-account and live only in their own profile.
- `cache/` - per-profile API discovery cache.

## Running a command against a profile

Always prefix with `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name>`.
The variable is documented in `gws --help` under ENVIRONMENT.

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name> \
  gws drive files list --params '{"pageSize": 10}'

GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name> \
  gws gmail users messages list --params '{"userId": "me", "maxResults": 5}'

GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name> \
  gws calendar events list --params '{"calendarId": "primary", "maxResults": 5}'
```

For a session-wide default, export once:

```bash
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name>
gws drive files list ...
```

## Adding a new profile (one-time per account)

`gws auth login` will refuse with `"No OAuth client configured"` if the
profile dir has no `client_secret.json`. Reuse the one from an existing
profile (it's the GCP OAuth client identity, safe to share across accounts):

```bash
# 1. Create the profile dir
mkdir -p ~/.config/gws/profiles/<name>

# 2. Reuse the OAuth client from your existing setup
cp ~/.config/gws/profiles/default/client_secret.json \
   ~/.config/gws/profiles/<name>/client_secret.json
# (or copy from any other profile that already has one)

# 3. Sign in (opens browser, pick the right Google account in the picker)
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name> gws auth login

# 4. Verify
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name> gws auth status
```

If you don't have a `client_secret.json` anywhere yet, run `gws auth setup`
(needs `gcloud`) to create a GCP project + OAuth client, or set
`GOOGLE_WORKSPACE_CLI_CLIENT_ID` / `GOOGLE_WORKSPACE_CLI_CLIENT_SECRET` env
vars per `gws auth login --help`.

For extra scopes (full Drive write, Pub/Sub, etc.) add `--full` or
`--scopes drive,gmail,calendar,...` to `auth login`.

## Listing / inspecting / deleting profiles

```bash
ls ~/.config/gws/profiles/
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/profiles/<name> gws auth status
rm -rf ~/.config/gws/profiles/<name>
```

## Notes for Claude

- When the user asks for a `gws` command, ask **which profile** if ambiguous.
  Account-to-profile mapping for this user is in `~/.claude/CLAUDE.local.md`.
- Mirror the env-var pattern above - do **not** create wrappers or aliases.
- Inline env-var prefix is preferred over `export` so the choice travels with
  the command and doesn't leak into subsequent unrelated calls.
- `credentials.enc` is keyring-encrypted (per-user secret); `client_secret.json`
  is the OAuth app identity (shareable across profiles).
