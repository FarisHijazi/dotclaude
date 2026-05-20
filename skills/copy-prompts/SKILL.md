---
name: copy-prompts
description: Copy all of MY prompts (just the user-typed messages from this conversation) to the clipboard and a temp file. Use when the user wants to extract or share their own prompts from the chat (e.g. "/copy-prompts", "copy my prompts", "save just my messages").
---

# Copy Prompts

Run the bundled standalone script to extract just the user-typed prompts from the current Claude Code session. It auto-detects the session JSONL via the cwd, filters out tool results / sidechains / meta entries, copies the result to the clipboard, and writes a copy to a randomized temp file.

```bash
python3 ~/.claude/skills/copy-prompts/extract_prompts.py
```

The script prints the temp-file path, clipboard tool used, and the source session filename. Pass that summary back to the user verbatim.

If the script reports the clipboard tool is unavailable, the file is still written — show the user the file path so they can `cat` or `open` it.
