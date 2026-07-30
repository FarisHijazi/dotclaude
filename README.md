# [dotclaude](https://github.com/FarisHijazi/dotclaude)

collection of AI dev tool techniques, prompts, flows, and tips for Claude Code but applicable to other tools.

```sh
cd ~/.claude && \
    git clone https://github.com/FarisHijazi/dotclaude && \
    mv dotclaude/.git . && \
    rm -rf dotclaude

# and then when ready to switch to the new changes:
git stash -m 'stashing changes before dotclaude git clone'
```


## Development


## This repo (dotclaude) tracking model

`.gitignore` is a **whitelist**: `/*` ignores every top-level entry, then `!/...`
re-includes only owned surfaces (`agents/`, `channels/`, `commands/`, `docs/`,
`hooks/`, `memory/`, `scripts/`, `skills/`, plus a few root files). Carve-outs
keep `get-shit-done/`, `skills/gsd-*`, `skills/handsfree`, `skills/gws/README.md`,
`skills/work-it-prep/`, `channels/inbox/`, and `*.local.*` out of the public
repo. See @docs/devlog/claude_2026-07-29-whitelist-gitignore.md.

