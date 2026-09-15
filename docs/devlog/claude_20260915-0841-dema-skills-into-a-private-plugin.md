# Moving the client skills out of a public repo, and what I found on the way

2026-09-15. Asked to deliver the client skills as a plugin instead of loose
files in `skills/`, test it on a machine that does not use them, merge the
diverged `CLAUDE.md` on the other VM, and commit `settings.json` without the
machine-local proxy URL.

## What was actually wrong

`README.md` already said work skills belong in their own private marketplace.
Two of them did not follow it: `skills/feat/` and `skills/remote-e2e/` were
tracked here, and **this repo is public**. They have been served from GitHub
since `771b9f4` (2026-08-19) and name nine distinct internal identifiers —
three build hosts, four repository names, the working directory layout, and the
cross-repo register lockstep between them.

Deleting them from the tip does not unpublish them. The commit stays fetchable.

### The credentials are worse

The pre-refactor copies of the `psql-*.sh` helpers carried their passwords as
literals, and those commits are ancestors of `origin/master` (2026-07-20 and
2026-08-19). Comparing a hash of each burned literal against the current value
in `~/.claude/.env`: **both are still the live passwords.** They were never
rotated.

A sweep of the fleet for `^export PGPASSWORD=` found plaintext copies still on
disk in three places — one machine's legacy skill directory and two copies in
`file-history/`, Claude Code's own undo store, which keeps the pre-edit version
of a file indefinitely. Editing a secret out of a file does not remove it from
that machine.

## The shape of the fix

A new **private** marketplace, `FarisHijazi/claude-plugins-private`, holding one
plugin, `dema`, with the three skills inside it.

The declaration is marked private with `settings-filter.sh privatize`, which
matters more than it first appears: `plugin marketplace add` clones the *whole*
marketplace repo, so leaving the declaration shared would have copied one
client's material onto the other client's VM the first time that box ran
`install-plugins.sh`. Private means the declaration lives only on the machines
that add it by hand, and `enabledPlugins` — already machine-local — decides
which of those switch it on.

`.gitignore` now carves out all three names, so a local copy cannot drift back
into a commit.

## Verified, not assumed

Installed on a machine that does no work for this client, and asked a real
session what it could see:

```text
connect-prod        dema-connect-prod   dema-feat
dema-remote-e2e     feat                remote-e2e
dema:connect-prod   dema:feat           dema:remote-e2e
```

Three facts fell out of that:

1. Plugin skills are namespaced — `feat` inside the `dema` plugin is
   `dema:feat`. That settles the collision a skill called `feat` invites, and
   it is why `feat/SKILL.md`'s two `@~/.claude/skills/...` force-loads had to be
   rewritten: those paths do not exist inside a plugin.
2. Both copies are offered at once until the unprefixed directory is deleted, so
   a migration has an ambiguous window.
3. `plugin uninstall` followed by `marketplace remove` reported success and left
   all 16 files in `plugins/cache/`. Since a session re-registers a plugin from
   exactly that cache, a leftover cache is not merely untidy. Removing the
   directory explicitly and re-asking gave a clean answer.

## settings.json

`settings-filter.sh` already kept `enabledPlugins` and privatized marketplaces
out of the repo. It now treats `env` the same way, because a base URL pointing at
a proxy on *this* box is a lie on the other three. Five round-trip cases pass in
a sandbox, including a fresh clone with no local snapshot.

`settings.json` therefore commits for the first time in a while, carrying only
`model` and `theme` — no proxy URL, no plugin list, no private marketplace.

One consequence to watch: `theme` is now tracked, and `cc-theme.sh` writes it.
Switching theme will dirty the repo.

## CLAUDE.md on the other VM

Not a merge. The backup was simply the pre-rewrite version: 240 verbose lines
against the current 193. Every distinctive token in it resolves to something
present — SOLID, the UART example, the `#NUMBER` rule, the whitespace rule, the
tests-skill conventions (under its current name, `pytests`). Two absolute
`/Users/...` paths in it are wrong on a Linux box and correctly relative now, and
the dropped `personal` placeholder was dropped deliberately. Nothing
machine-specific, nothing to merge, no conflicts to resolve.

## Postscript: `theme` had to join `env`

Committing `theme` lasted exactly one machine. The first VM to pull hit a
three-way conflict on that single line — upstream `light`, its own `auto` — and
`cc-theme.sh` writes the key, so every theme switch on any machine would have
produced the same conflict on the other three.

The filter's `env` handling is now a `LOCAL_KEYS` list holding `env` and `theme`,
merged back per key by type (objects merge, scalars replace). The test that
matters: two settings files differing only in `theme` now `clean` to identical
bytes, so there is nothing left to conflict over.

## A second plugin: the security command set

Same private marketplace, a `security` plugin holding the 23 bug-bounty /
pentest commands and 10 skills that were loose under `commands/` (and already
gitignored). One switch now installs, enables, disables and uninstalls the whole
set, and it ships **disabled by default**.

The migration mattered more than the packaging. Those commands were live in
`~/.claude/commands/` on every session; a plugin left disabled has to actually
remove the loose copies or nothing changes. Confirmed both directions against a
real session: disabled → `/autopilot` is gone; enabled → it returns as
`security:autopilot` (plugin commands are namespaced, like the skills). A tarball
backup of all 43 files sits at `~/.claude-security-loose-backup-*` in case the
plugin ever needs rebuilding from the originals.

The bundling scope was drawn from the `.gitignore` pen-testing list, not from
"every loose `.md`" — a first pass swept in seven unrelated commands
(`wrapup`, `wt`, `auto-compact`, …) that a diff against the list caught before
anything was committed.
