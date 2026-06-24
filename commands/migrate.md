---
argument-hint: <new_path>
description: Migrate conversation history after moving this project to a new directory
---

# Migrate Claude Code History

The user has moved (or is about to move) this project to a new directory. Run the migration script to copy the conversation history so `claude --continue` works at the new location.

**Old path (current):** The current working directory (use `pwd`)
**New path:** $ARGUMENTS

Run this command:
```
uvx git+https://github.com/FarisHijazi/claude-migrate migrate "$(pwd)" "$ARGUMENTS"
```

If the user wants you to also copy/move the actual project folder (not just the history), add `--folder` and any of these:
- `--delete-history` (move history instead of copy)
- `--delete-dir` (also delete the source folder — requires `--folder`)
- `--replace-userpath` (rewrite `/Users/<user>` in chat content; auto-detects, or pass `--replace-userpath=alice:bob`)
- `--replace-references` (rewrite absolute and relative path references inside chat content)

After running, tell the user:
1. The history has been copied
2. They can now `cd $ARGUMENTS && claude --continue` to resume
