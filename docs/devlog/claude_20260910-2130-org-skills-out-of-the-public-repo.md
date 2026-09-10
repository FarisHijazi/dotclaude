# A work skill that an org marketplace already owned, published here as well

2026-09-10. `skills/connect-prod/` — 11 files — was tracked in this **public**
repo. It is byte-identical to the copy in a client org's **private** plugin
marketplace, which already owns it.

## Why the duplicate mattered

The credentials had already been taken out (they now come from `~/.claude/.env`),
so the obvious risk was gone. What was left is the part that is easy to miss:

- ~27 internal `10.x` addresses
- a 16 KB production log catalogue and 10 KB of incident investigations
- Grafana dashboard JSON, and shell tooling that names the databases, roles and
  services it connects to

None of that is a secret in the "rotate it" sense. All of it is a map of someone
else's private infrastructure, and it was published under a personal account.

A duplicate is also worse than a link on its own terms: two copies of a skill
means only one of them gets updated, and the stale one is the one people find
by accident.

## What changed

`git rm --cached` (the working copy stays, nothing breaks locally), plus a
`.gitignore` carve-out so a local copy cannot drift back into a commit. The
canonical copy stays in the org marketplace and is installed from there like any
other plugin.

## The rule

Before adding a skill here, check whether an org marketplace already owns it.
A skill that exists to operate a client's or an employer's infrastructure
belongs in that org's marketplace, not in a personal public repo — the
hostnames, internal addresses and incident notes are the sensitive part, not
just the passwords.

This is the same "find who already owns it" check that applies to code, applied
to skills. Related: `docs/devlog/claude_20260910-2015-plugin-state-out-of-git.md`
for how marketplaces are scoped per machine.

## Not fixed here

Three sibling skills (`feat`, `merge-deploy-test`, `remote-e2e`) are in the same
position — two of them byte-identical to the org's copies, one differing by four
lines — and one of them carries internal dev hostnames. They were left tracked
pending a decision.
