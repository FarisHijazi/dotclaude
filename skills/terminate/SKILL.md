---
name: terminate
description: Immediately terminate the current Claude Code session
allowed-tools:
  - Bash
---

Immediately terminate this Claude Code session by running:

```bash
kill $PPID
```

Do NOT ask for confirmation. Do NOT print anything before running the command. Just run it.

