---
name: Python monkey-patching with from-imports
description: When monkey-patching a function, patch it where it's used (the consumer module), not where it's defined (the source module), because `from X import Y` copies the reference.
type: feedback
---

When monkey-patching a Python function, always patch it **in the module that calls it**, not just in the module that defines it. `from src.utils.telemetry import push_telemetry` copies the function reference into the importing module's namespace. Patching the source module (`_tel.push_telemetry = new_fn`) doesn't affect modules that already imported it via `from ... import`.

**Why:** This caused a silent production bug where every telemetry push from miner child processes failed — the monkey-patch was applied to `src.utils.telemetry.push_telemetry` but `src.actors.miner` had its own copy from the `from` import.

**How to apply:** When monkey-patching, always check how the target function is imported in the consumer module. If it uses `from X import Y`, patch `consumer_module.Y`, not `X.Y`.
