# [dotclaude](https://github.com/FarisHijazi/dotclaude)

collection of AI dev tool techniques, prompts, flows, and tips for Claude Code but applicable to other tools.

```sh
cd ~/.claude && \
    git clone git@github.com:FarisHijazi/dotclaude && \
    mv dotclaude/.git . && \
    rm -rf dotclaude

# and then when ready to switch to the new changes:
git stash -m 'stashing changes before dotclaude git clone'

# REQUIRED, once per machine — see "Per-machine plugin state" below:
bash scripts/install-git-filters.sh

# plugins are declared in settings.json but NOT cloned with it; this installs them:
bash scripts/install-plugins.sh
```

## Development

## This repo (dotclaude) tracking model

`.gitignore` is a **whitelist**: `/*` ignores every top-level entry, then `!/...`
re-includes only owned surfaces (`agents/`, `channels/`, `commands/`, `docs/`,
`hooks/`, `memory/`, `scripts/`, `skills/`, plus a few root files). Carve-outs
keep `get-shit-done/`, `skills/gsd-*`, `skills/handsfree`, `skills/gws/README.md`,
`skills/*-it-prep/`, `skills/connect-prod/`, `channels/inbox/`,
`**/.cc-convos/`, and `*.local.*` out of the public repo. See `docs/devlog/claude_2026-07-29-whitelist-gitignore.md`
(deliberately a plain path, not an `@` include).

### Driving the TUI from a script

Two settings a running session will not re-read: `theme` and the per-session
colour. Editing `settings.json` only affects the NEXT session, so the one lever
is the slash command, typed into the pane.

- `scripts/cc-theme.sh <name> [target]` — set a live session's theme
  (`auto`, `dark`, `light`, and the `-daltonized` / `-ansi` variants);
  `--list` prints the menu and marks the active entry.

It does not count arrow presses. The `/theme` popup opens with the cursor on the
*current* theme, so any fixed number of Up/Down is wrong from every other
starting point — and the list grows when you save a custom theme. The menu is
numbered and a digit selects directly, so the script reads the menu off the
pane, matches the label exactly, and presses that digit.

Anything that types into a pane must hold the cc-notify type-lock and verify
against the pane rather than a single `cc-prompt-state` read — a recognised
slash command is drawn coloured, and an open menu hides the input box
altogether. `hooks/auto-compact-continue.sh` and cc-notify's `cc-color-apply.sh`
are the two worked examples.

### Plugins are declared here, materialised elsewhere

`settings.json` carries only the *names*: `extraKnownMarketplaces` and
`enabledPlugins`. The marketplace clones and plugin payloads live in
`~/.claude/plugins/`, which is untracked because it stores absolute paths and
can embed a PAT in a marketplace URL. Cloning this repo therefore reproduces the
declaration and not the thing it names — which is what *cache miss* means.

`scripts/install-plugins.sh` closes the gap: it reads the tracked
`settings.json`, installs whatever is missing, and lists anything installed but
undeclared. It is idempotent, so it is also the fix to run when a plugin or
marketplace reports a cache miss. `--dry-run` prints the plan.

Which file to look at for which error, what `~/.claude.json` holds, why
claude.ai connectors need none of this, and the `syncClaudeAiPlugins` /
`syncClaudeAiSkills` account-sync alternative:
`docs/plugins-mcp-and-connectors.md` (deliberately a plain path, not an `@`
include).

### Per-machine plugin state

`settings.json` is shared, but its `enabledPlugins` key is not: it records which
plugins *this* machine has installed, and Claude Code rewrites the file to drop
anything it cannot resolve. Committing it makes one machine's list overwrite
everyone's.

A git clean/smudge filter keeps that one key out of the repo and restores this
machine's copy from the untracked `settings.plugins.local.json`. **Filters are
per-clone — a repo cannot configure its own** — so `install-git-filters.sh` above
is not optional. A `.gitattributes` entry naming a filter that git config does
not define is silently a no-op: the key gets committed and nothing warns you.

```sh
bash scripts/settings-filter.sh show      # what this machine owns
bash scripts/settings-filter.sh save      # after enabling/disabling plugins
git checkout -- settings.json             # re-apply the snapshot
bash scripts/settings-filter.test.sh      # 32 assertions, touches nothing real
```

`extraKnownMarketplaces` is **shared by default** — most marketplaces belong on
every machine. A marketplace that belongs to one machine only is opted out:

```sh
bash scripts/settings-filter.sh privatize <marketplace>   # this machine only
bash scripts/settings-filter.sh share <marketplace>       # undo
git add --renormalize settings.json
```

Shared-by-default is the safe direction. A session that cannot resolve a
marketplace rewrites `settings.json` without it, so an un-privatized entry gets
pruned for *every* machine at once — which is exactly how a marketplace and four
plugins silently disappeared from the shared file once already.

Install plugins per machine with `claude plugin install <plugin>@<marketplace>`.
Never copy `plugins/*.json` between machines — they index **absolute** paths and
will break every plugin on a host with a different home directory.

Full writeup: `docs/devlog/claude_20260910-2015-plugin-state-out-of-git.md`.

### Work skills belong to their own marketplace

A skill that exists to operate a client's or employer's infrastructure does not
belong in a personal public repo, even with no credentials in it: the hostnames,
internal addresses, log catalogues and incident notes are the sensitive part.
Those live in that org's own private plugin marketplace and are installed from
it like any other plugin, and the name is carved out of `.gitignore` here so a
local copy cannot drift back into a commit.

Before adding a skill here, check whether an org marketplace already owns it —
a duplicate is worse than a link, because only one of the two gets updated.

Current marketplaces of this kind, all declared **private** so they are stripped
from this repo and reach only the machines that add them:

| Marketplace | Plugin | Install on |
| --- | --- | --- |
| `dema-skills` (`DEMAEnergy/dema-skills`) | `dema-dfc` — connect-prod, feat, remote-e2e, merge-deploy-test | a machine doing that client's work |
| `thmanyah-skills` (`Thmanyah-LLC/…`) | `thmanyah-arabic` | likewise |
| `farishijazi-private` | `security` — personal pentest set, disabled by default | any machine, on demand |

```bash
claude plugin marketplace add <owner>/<repo>
claude plugin install <plugin>@<marketplace> -y
scripts/settings-filter.sh privatize <marketplace>   # keep it out of this repo
git add --renormalize settings.json
```

A client's skills belong in **that org's own** private marketplace
(`DEMAEnergy/dema-skills`, `Thmanyah-LLC/…`), never a personal account — the org
owns and maintains them. A personal private marketplace is only for personal
plugins. `privatize` matters more than it looks: `plugin marketplace add` clones the
**entire** marketplace repo, so a shared declaration would copy one client's
content onto the other client's VM the moment that machine ran
`install-plugins.sh`.

Two behaviours worth knowing when moving a skill into a plugin:

- A plugin namespaces its skills, so `feat` becomes `dema-dfc:feat`. Until the
  old unprefixed copy is deleted, both are offered at once.
- `plugin uninstall` and `marketplace remove` both leave the payload in
  `plugins/cache/<marketplace>/`. If the point was to get the content off the
  machine, delete that directory too.
