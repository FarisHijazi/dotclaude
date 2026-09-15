# Plugins, MCP servers and connectors — what is a file, what is not

Why this doc exists: cloning this repo onto a second machine reproduces
`settings.json` but **not** the machine-local state it points at, so plugins
report *cache miss*. This explains exactly which bytes live where.

Everything below was verified against Claude Code **2.1.270** on 2026-09-14,
by experiment in a throwaway `$HOME` (see "Experiments" at the end), not from
memory.

## The one idea

Claude Code splits every plugin into a **declaration** and a
**materialisation**, and they live in different files with different fates:

| | Declaration | Materialisation |
|---|---|---|
| File | `settings.json` | `plugins/known_marketplaces.json`, `plugins/installed_plugins.json` |
| Keys | `extraKnownMarketplaces`, `enabledPlugins` | `installLocation`, `installPath` |
| Contents | repo names — portable | **absolute paths** + git SHAs — machine-only |
| Tracked here? | **yes** | **no**, and must never be |
| Written by | `plugin marketplace add` / `plugin install` | the same commands |

`plugin install` writes **both**. That is the useful part: you never hand-write
the declaration, the CLI maintains it, so a tracked `settings.json` is already
an accurate manifest of what the machine should have.

The trap is the other direction: **the declaration does not rebuild the
materialisation.** A `settings.json` listing ten plugins on a machine with an
empty `plugins/` installs nothing, silently, forever.

One partial exception, worth knowing because it looks like magic: at session
start Claude Code reconciles `installed_plugins.json` against `enabledPlugins`
("Syncing installed_plugins.json with enabledPlugins from all settings.json
files"). That heals a plugin **whose payload is already sitting in `cache/`**
but which the registry had lost — purely local, no network, works even
unauthenticated. It never fetches. So a stale registry fixes itself and a
missing download never does.

## What each file under `plugins/` is

| Path | Holds | Rebuildable? |
|---|---|---|
| `known_marketplaces.json` | registered marketplaces + absolute `installLocation` + **any PAT embedded in a git URL** | yes, `plugin marketplace add` |
| `installed_plugins.json` | per-plugin `installPath`, `version`, `gitCommitSha`, `scope` | yes, `plugin install` |
| `marketplaces/<name>/` | the cloned marketplace repo | yes, re-clone |
| `cache/<mkt>/<plugin>/<version>/` | the plugin itself; **every version ever installed is kept** | yes, re-download |
| `config.json` | `{"repositories":{}}` — link-mode repos | n/a |
| `plugin-catalog-cache.json` | downloaded catalogue (~500 KB here) | yes |
| `blocklist.json` | plugins you blocked | preference, tiny |

`known_marketplaces.json` can contain a credential — a marketplace added over
HTTPS stores the whole URL including the token. That alone makes `plugins/`
un-trackable, on top of the absolute paths.

## The three "cache miss" messages

These are distinct errors with distinct fixes. Strings taken from the binary:

| Error | Message | Fix |
|---|---|---|
| `plugin-cache-miss` | `Plugin "X" not cached at <installPath>` | `/plugin` to refresh the plugin cache |
| `marketplace-load-failed`, reason `cache-miss` | `Failed to load marketplace "X": cache-miss` | `/reload-plugins` to refresh the marketplace cache |
| `marketplace-not-found` | `Marketplace "X" not found` | check `known_marketplaces.json`, then `/reload-plugins` |

Read the noun. *Plugin* cache miss = `installed_plugins.json` names an
`installPath` that is not on disk. *Marketplace* cache miss = the clone under
`marketplaces/` is gone or unreadable. The first is per-plugin, the second
takes every plugin from that marketplace down with it.

A fourth state produces no cache miss at all and is easy to miss: a plugin
`true` in `enabledPlugins` but **absent from `installed_plugins.json`**. It
does not appear in `plugin list` even when its cache directory is fully
populated — the registry, not the cache, is what `list` reads. This one is
self-correcting: the next session start re-registers it (see above), so it can
look like the problem fixed itself while you were reading about it.

The inverse — registry entry present, `installPath` gone — is the true
`plugin-cache-miss`, and it does **not** self-correct. `install-plugins.sh`
reports these; `--prune-missing` drops the dead records.

## MCP servers: four places, one precedence order

| Scope | File | Key | Portable? |
|---|---|---|---|
| project | `<repo>/.mcp.json` | `mcpServers` | **yes** — commit it |
| user | `~/.claude.json` | `.mcpServers` | no |
| local (per project) | `~/.claude.json` | `.projects["<abs path>"].mcpServers` | no — keyed by absolute path |
| plugin | `<plugin>/.mcp.json` | `mcpServers` | travels with the plugin |

Tool-name prefix tells you which one you are looking at: a directly-added
server is `mcp__<name>__*`, a plugin-provided one is
`mcp__plugin_<plugin>_<server>__*`. Two servers pointing at the same endpoint
by both routes show up as two tool families.

`~/.claude.json` is the problem file: ~200 KB of machine state, absolute
`command`/`args` paths, plaintext `env` secrets, and a `projects` map keyed by
absolute path. Never track it. A directly-added MCP server has to be re-added
per machine; a plugin-provided one rides along with `plugin install`.

**That is the single best reason to prefer a plugin over a direct MCP add**
when the server is something you want on every machine.

### Credentials

`~/.claude/.credentials.json` holds `claudeAiOauth` (your login) and `mcpOAuth`
(per-server tokens, keyed `<serverName>|<hash of server URL>`). The hash is
derived from the URL, so the same server has the same key on every machine —
which makes the file look copyable. It is not: never track it, never rsync it.
Re-auth per machine with `/mcp`.

## claude.ai connectors (Gmail, Calendar, Drive…)

Not files. They are bound to the Anthropic **account**, fetched at session
start, and appear as `mcp__claude_ai_*`. Nothing to sync, nothing to clone —
log in on a new machine and they are there. They require subscription auth; an
`ANTHROPIC_API_KEY` session does not get them.

Being account-bound cuts both ways here, where the login is switched often: the
connector set is whichever account is active, not whichever machine you are at,
and it changes under you on every switch. That is a feature for Drive and Gmail
(you want the active identity's mail) and the reason plugins must *not* work the
same way — see the next section.

Where they interact with the local world: if a connector and a plugin expose
the same endpoint, the plugin's server is **suppressed** as a duplicate
(`[MCP] Lazy dedup: suppressing N plugin server(s) that duplicate claude.ai
connectors`). So a plugin can look broken when it is merely deduplicated.

## Native account sync — deliberately off

Two settings keys exist and default to **false**:

```json
{ "syncClaudeAiSkills": true, "syncClaudeAiPlugins": true }
```

With these on, skills and plugins follow the **account** instead of the
filesystem — Anthropic's own answer to this problem, and on the face of it a
replacement for everything above. (Unrelated to `/cloud-plugins`, which only
decides whether *this* machine's plugins are forwarded to a cloud session.)

**Do not turn these on here.** Accounts get switched frequently on all three
machines, so account-scoped state is the one axis that does *not* stay put: the
plugin set would change under you every time the active login changed, and the
thing it changed to would depend on which account you happened to be on rather
than which machine you were at. Git is the right carrier precisely because a
checkout is per-machine and does not move when the login does. Evaluated and
rejected 2026-09-15 — do not re-propose without that constraint changing.

## Recommended split

Track the declaration, script the materialisation, never track the state.

1. **Track** `settings.json` (`enabledPlugins` + `extraKnownMarketplaces`) —
   it is already maintained for you by `plugin install`.
2. **Never track** `plugins/`, `~/.claude.json`, `.credentials.json`.
3. **Bootstrap** a new machine from the declaration with
   `scripts/install-plugins.sh`, which reads the tracked `settings.json` and
   runs `plugin marketplace add` / `plugin install` for anything missing. It is
   idempotent, so it is also the repair tool for a cache miss.
4. **Per-machine plugins** (`grafana-mcp` on one VM only) — keep the marketplace
   private with `scripts/settings-filter.sh privatize`, per
   [README](../README.md).

## Experiments that establish the above

Run with a throwaway `HOME`, so nothing real is touched:

- From `settings.json == {}`, `plugin marketplace add cloudflare/skills`
  followed by `plugin install cloudflare@cloudflare` produced both
  `extraKnownMarketplaces` and `enabledPlugins` in `settings.json`
  (→ the CLI maintains the declaration).
- With that `settings.json` intact but `plugins/` deleted, `plugin list` says
  *No plugins installed* and `plugin marketplace list` says *No marketplaces
  configured*; nothing is re-created (→ declarations do not self-heal).
- Booting a session in that state re-creates only the scaffolding —
  `plugins/`, an empty `marketplaces/`, and `installed_plugins.json` as
  `{"version":2,"plugins":{}}`. Not the marketplaces, not the plugins.
- Repeating that boot with `cache/` and `marketplaces/` populated but
  `installed_plugins.json` emptied, the session **re-registered** the plugin
  (`[]` → `["cloudflare@cloudflare"]`) while still unauthenticated (→ the
  registry heals from the cache locally; only the download needs the network).
  This is why a plugin can vanish from `plugin list` and reappear on its own.
