---
name: Find the existing owner
description: Extend the owner of shared behavior instead of adding a competing implementation.
type: feedback
---

- Find the responsible service or module in code and relevant repository instructions before adding a writer, listener, cache or poller.
- Extend or fix that owner. Reuse behavior that differs only by data; keep distinct locking, invariants or failure semantics separate.
- Preserve the same authorization and safety gates across typed and raw entry points. Passive config, health and telemetry paths must not bypass the command path.
- Reject unsupported changes explicitly and identify who corrects a detected fault; do not silently skip work or imply a diagnostic fixed it.
- Resolve ownership conflicts explicitly rather than rewriting an invariant to hide a violation. Use this check to guide ordinary work, not stall it.
