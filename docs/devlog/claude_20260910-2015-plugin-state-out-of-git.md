# Keeping per-machine plugin state out of a shared settings.json

2026-09-10. Three machines share this repo: the Mac and two Debian boxes.

## What broke

Every plugin on one Debian box failed to load with `cache-miss`, and
`/plugin marketplace update <name>` could not repair it.

The cause was **not** git. `~/.claude/plugins/` is ignored; only `settings.json`
is tracked. So the plugin *declarations* (`enabledPlugins`) synced while the
plugin *installations* did not — and the registry had been made worse by hand:
`plugins/known_marketplaces.json` and `plugins/installed_plugins.json` had been
copied over from the Mac, and both store **absolute paths**. Every entry pointed
at `/Users/<mac-user>/...` on a box whose home is `/home/<user>`. Nothing on disk
matched, so every lookup missed.

### Do not do this

- **Never copy `plugins/*.json` between machines.** They are a machine-local
  index of absolute paths, not portable config.
- **Never commit `enabledPlugins`.** Machine A's list disables plugins machine B
  actually has, and the next session on B rewrites the file to match what it can
  resolve — silently dropping entries for everyone.

### Do this instead

Install plugins per machine with the CLI, and let each machine own its own list:

```sh
claude plugin marketplace add <owner>/<repo>
claude plugin install <plugin>@<marketplace>
claude plugin list
```

If a registry is already corrupt, rewrite the home prefix in both JSON files
(back them up first) or remove and re-add the marketplace.

## The fix: a clean/smudge filter

`enabledPlugins` is per-machine state living inside an otherwise-shared file, and
it cannot be moved out: **there is no user-level `settings.local.json`.** Claude
Code reads project-local overrides, not user-local ones. So the key stays where
it is and git is taught to ignore it:

| direction | what runs | effect |
|---|---|---|
| worktree → index | `settings-filter.sh clean` | strips `enabledPlugins`; the repo copy never has it |
| index → worktree | `settings-filter.sh smudge` | merges this machine's `settings.plugins.local.json` back in |

`.gitattributes` carries `/settings.json filter=claude-settings`; the filter
bodies live in git config. See `scripts/settings-filter.sh` and
`scripts/install-git-filters.sh`. The mirror-image problem for the untracked
`~/.claude.json` is solved by `scripts/apply-overrides.sh`.

A `pre-commit` hook (`no-plugin-state-in-settings`) checks the **staged blob**,
not the worktree file — `git show :settings.json | jq -e 'has("enabledPlugins")'`
— so it catches a machine whose filter was never installed.

## Traps found while building it

1. **Filters are per-clone by design.** A repo cannot configure its own filters
   (that would let any clone run code on checkout). `.gitattributes` naming a
   filter that git config does not define is **silently a no-op** — git does not
   warn, it just writes the file through unchanged. Every new machine must run
   `scripts/install-git-filters.sh` once, or it will commit its plugin list.

2. **Bootstrap order.** On a machine that pulls *before* installing the filter,
   `settings.json` arrives with no `enabledPlugins` at all. A naive `save` at
   that moment snapshots nothing and wipes the very thing it was meant to
   preserve. `save` therefore refuses to overwrite a non-empty snapshot with an
   empty one, and a separate `restore` merges the snapshot back into a
   `settings.json` that a checkout wrote without the key.

3. **`git add --renormalize` is required.** Git re-runs a filter only when it
   thinks the file changed, so an already-tracked `settings.json` keeps its old
   key-carrying blob until it is renormalized.

4. **`jq -s '.[0] * .[1]'` cannot express a removal.** `*` deep-merges objects,
   so merging a 7-entry list over an 11-entry one yields 11, not 7. This is
   correct *inside* smudge — the index copy has already had the key stripped, so
   there is nothing to merge against and the snapshot wins outright — but any
   ad-hoc merge against a settings.json that still holds the key silently
   resurrects deleted entries. Use `+` (shallow, right side replaces the key) to
   set a list wholesale. `restore` is safe because it is guarded to run only when
   the key is absent.

5. **`git status` shows `M` after any local plugin change while `git diff` is
   empty.** The cleaned content is identical; only the stat cache is stale, and
   `git update-index --refresh` does not clear it. A plain
   `git add settings.json` refreshes the entry and status goes clean, staging
   nothing. This is not drift — do not "repair" it with `git checkout`.

## Recovering a machine whose plugin list looks wrong

```sh
bash scripts/settings-filter.sh show          # what this machine claims to own
git checkout -- settings.json                 # re-runs smudge from the snapshot
```

If the *snapshot* is the stale one, edit `settings.json` to the truth and
`bash scripts/settings-filter.sh save`. Saving is what makes a removal stick;
editing `settings.json` alone is undone by the next checkout.

## Result

All three machines on one commit, each keeping its own plugin set — Mac 11,
one box 7, the other 8 — and `git status` clean on all three.
