---
argument-hint: export | import <archive> [path] | cp <old> <new> | mv <old> <new> | rm <path>
description: Migrate conversation history — export/import between machines or copy/move/remove
---

# Migrate Claude Code History

Thin wrapper around `claude-migrate`. Run the user's subcommand via:

```
uvx git+https://github.com/farishijazi/claude-migrate.git $ARGUMENTS
```

If `$ARGUMENTS` is empty, run with `--help` to show usage.

After running, summarize the output to the user.
