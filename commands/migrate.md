---
argument-hint: <new_path> | [user@]host:<new_path>
description: Migrate Claude Code conversation history after moving a project — to a new local path or to another machine over ssh
---

# Migrate Claude Code History

The user moved (or is about to move) this project. Copy its conversation history
so `claude --continue` works at the destination.

**Source:** the current working directory (`pwd`)
**Destination:** $ARGUMENTS

## Always use the git URL

```
uvx git+https://github.com/FarisHijazi/claude-migrate <subcommand> ...
```

`uvx` fetches and runs it in one step, so there is nothing to install first.

**Never use `uvx claude-migrate`.** The PyPI build lags and ships only
`cp`/`mv`/`rm`/`install-slash` — it has **no `export`/`import`**, which the
remote path below depends on. The tool's own success message suggests the PyPI
form; ignore it. Confirm with `--help` if a subcommand appears to be missing.

## Pick local or remote

If `$ARGUMENTS` contains a `:` before the path (`host:/path`, `user@host:/path`),
it is **remote**. Otherwise it is **local**.

### Local — same machine, new path

```bash
uvx git+https://github.com/FarisHijazi/claude-migrate cp "$(pwd)" "<new_path>"
```

Use `mv` instead of `cp` if the user wants the old history removed rather than
kept. Add `--merge` when the destination already has history, and run once with
`--dry-run` first to preview.

### Remote — another machine over ssh

Run these in order, substituting `<host>` and `<remote_path>` from `$ARGUMENTS`.
Rely on `~/.ssh/config` for the key; if the user gave one, thread the same
`-i <key>` through both `ssh` and `scp`.

```bash
# 1. archive this project's history locally
uvx git+https://github.com/FarisHijazi/claude-migrate export "$(pwd)" -o /tmp

# 2. copy it over  (use the exact filename the export printed)
scp /tmp/<archive>.tar.gz <host>:/tmp/

# 3. make sure uvx exists there — installs in seconds, no other setup.
#    Set PATH FIRST: uv installs to ~/.local/bin, and a non-interactive ssh
#    does not source .bashrc, so an unguarded `command -v uvx` reports MISSING
#    even right after a successful install (and would reinstall every run).
ssh <host> 'export PATH="$HOME/.local/bin:$PATH"
  command -v uvx >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh'

# 4. import: re-keys the history to the remote path AND rewrites the old
#    absolute path inside the transcript text
ssh <host> 'export PATH="$HOME/.local/bin:$PATH"
  uvx git+https://github.com/FarisHijazi/claude-migrate import \
    /tmp/<archive>.tar.gz "<remote_path>"'
```

Every remote command needs that `export PATH` prefix, not just the install
check — `uvx`, and `claude` itself, both live in `~/.local/bin`.

Run step 4 with `--dry-run` first when the destination may already have history.

Do **not** hand-roll this with `scp -r` of `~/.claude/projects/<dir>`. History
directories are named after the project's absolute path, so a plain copy lands
under a name the remote never looks up — and it skips the in-transcript path
rewriting, leaving thousands of stale source paths embedded in the chat text.

### Conflicts

A merge onto existing history reports `conflict: N` and writes `.incoming`
files alongside the originals. Show the user the counts and resolve explicitly —
the `.incoming` version is the freshly rewritten one, so it is usually the
keeper:

```bash
ssh <host> 'cd ~/.claude/projects/<slug> && find . -name "*.incoming"'
```

Never leave `.incoming` files behind silently.

## Then verify, don't assume

```bash
ssh <host> 'export PATH="$HOME/.local/bin:$PATH"; cd <remote_path>
  claude --continue -p "In one line, what were we last working on?"'
```

A real answer means the history is genuinely wired up. Report to the user:

1. where the history landed (the target slug the tool printed)
2. any conflicts and how they were resolved
3. that they can `cd <destination> && claude --continue`

## Scope

This moves **history only**. If the user also wants settings, skills, commands,
hooks, credentials or the project files themselves carried to another machine,
that is the `claude-machine-migrate` skill — use it instead, and it will call
back into this flow for the history step.
