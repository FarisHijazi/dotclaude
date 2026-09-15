# Why plugins "cache miss" on a fresh clone, and what now fixes it

Question that started it: cloning this repo onto the VMs leaves some plugins and
MCP servers failing with *cache miss*, and it was not clear how a plugin MCP, a
directly-added MCP and a claude.ai connector differ in terms of files.

Durable answer: `docs/plugins-mcp-and-connectors.md`. Tool:
`scripts/install-plugins.sh`. This file is the working, including the two things
I got wrong on the way.

## The model

Claude Code splits a plugin into a **declaration** (`settings.json` →
`extraKnownMarketplaces`, `enabledPlugins` — names only, tracked) and a
**materialisation** (`plugins/known_marketplaces.json`,
`plugins/installed_plugins.json`, `marketplaces/`, `cache/` — absolute paths,
git SHAs, sometimes a PAT, never tracked). Cloning brings the first and not the
second. That is the whole bug.

The convenient half: `plugin marketplace add` and `plugin install` write **both**
sides, so the tracked `settings.json` is a self-maintaining manifest and is never
hand-edited. Verified from `{}`.

## Correction 1 — "nothing self-heals" was too strong

I wrote that first and it is wrong. Startup reconciles
`installed_plugins.json` against `enabledPlugins`, but only for a plugin whose
payload is **already in `cache/`**. Local, no network, works unauthenticated.

I only caught it because three plugins on the laptop (`swift-lsp`, `amplitude`,
`slack`) were enabled-but-unregistered when I looked, and registered when I
looked again twenty minutes later. Confirmed deliberately: emptied the registry
in a throwaway `$HOME` with the cache left in place, booted an unauthenticated
session, and `installed_plugins.json` went `[]` → `["cloudflare@cloudflare"]`.

So: **a lost registry entry fixes itself; a missing download never does.** The
earlier experiment that "proved" no self-heal had an empty cache, so there was
nothing to heal from — the experiment was fine, the generalisation was not.

## Correction 2 — the script could not see the actual error

v1 compared declaration to registry. But `plugin-cache-miss` is registry
vs **disk**: a record whose `installPath` is gone. v1 was structurally blind to
the one error the question was about, and reported both VMs as healthy while
each carried a real miss (`claude-mem@thedotmack`, path deleted).

v2 checks it, and branches on whether the plugin is still declared: still
declared → reinstall; not declared → dead record, reported, and dropped only
under `--prune-missing`.

## The four states, because only two are errors

| Registry | Disk | Result |
|---|---|---|
| present | present | fine |
| absent | present | invisible to `plugin list`; **self-heals** next session |
| present | absent | `plugin-cache-miss`; never self-heals — this is the one |
| absent | absent | declared but never installed; `install-plugins.sh` installs it |

## Rejected: `syncClaudeAiPlugins` / `syncClaudeAiSkills`

Real settings keys, default false, and on paper they replace this whole
mechanism by binding plugins to the account. Rejected: accounts are switched
frequently on every machine here, so the plugin set would change with the active
login rather than staying with the machine. A git checkout is per-machine and
does not move when the login does. Recorded in the doc so it is not re-proposed.

Worth noting the asymmetry — claude.ai **connectors** are account-bound and that
is correct for them (you want the active identity's Drive and mail). Plugins are
tooling and should follow the machine.

## Outcome

All three machines verified clean: no registry record points at a missing path,
no declared plugin is unmaterialised. Neither VM needed an install — their
`settings.json` had already been pruned by hand down to what actually worked,
which in hindsight was the manual version of what this script now does properly.

Left alone deliberately: dema's uncommitted `settings.json` prune (confirmed
intentional), thmanyah's `model: fable`, and two unregistered marketplace
directories on dema (`claude-code-plugins`, 33 MB, a clone of a public repo;
plus an empty one whose name ends in a space) — unreferenced, harmless, and not
mine to delete unasked.
