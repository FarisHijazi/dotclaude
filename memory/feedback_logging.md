---
name: Log actual values, not hardcoded strings
description: When logging variable state, use f-strings with the actual value instead of hardcoding assumed values like "=false"
type: feedback
---

Log actual runtime values using f-strings, not hardcoded assumptions.

**Why:** A log line like `'power_setpoints_enabled=false — blocked %s call'` hardcodes the value instead of showing what it actually is (could be `None`, `False`, etc.). User called this "horrible."

**How to apply:** When logging a variable's state (especially in guard/gate conditions), always interpolate the actual value: `f'power_setpoints_enabled={self.power_setpoints_enabled!r} — blocked {endpoint} call'`. Use `!r` for unambiguous representation.
