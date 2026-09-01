---
name: Never render absent data as an answer
description: Frontend rule — not-yet-loaded and genuinely-empty are different facts. Gate on a sticky hasLoaded first-settle flag, never on !loading, and never show empty state, zeros, or a FALSE branch mid-flight.
type: feedback
---

A UI must never present a value derived from data that has not arrived. Rendering the empty case
while a request is in flight is not showing "nothing" — it is **asserting** nothing, with the same
confidence as the real value. Show a spinner/skeleton until the first response has SETTLED.

**Forbidden before first settle:** empty-state copy ("No results", "Nothing recorded"); zero counts
and totals; `—` / `n/a` / `unknown` / `never`; a chart from an empty series (reads as a flat line at
zero, i.e. "the system is dead"); a boolean shown via its FALSE branch (a toggle sitting OFF, a badge
reading "disconnected"); a status or mode defaulting to something benign; and any verdict computed
from those. Controls whose true state is unknown must be **disabled**, not merely labelled — an
operator who can flip a switch before its state loaded acts on a value that was never real.

**The specific trap, and it is everywhere:** `const [loading, setLoading] = useState(false)` plus
data initialised to `[]`/`null`. `loading` only flips true once a fetch *starts* — for an
authenticated fetch, after the session hydrates. In that gap `loading === false` and the data is
empty, which together read as "the query ran and the answer is nothing."

**How to apply:**
- Gate on a separate first-settle flag (`hasLoaded`), not on `!loading`.
- Make it **sticky**, so a poll or filter change doesn't flash a live view back to a skeleton.
- Set it in the `finally` (an error settles too), and settle it explicitly when no request will ever
  be made (feature disabled, no id to fetch, auth resolved with no token) — otherwise a lie has been
  replaced with a hang, which is worse.
- **Verify the loading affordance is actually visible.** A skeleton styled with a design token the
  project never defined compiles fine, generates no CSS, and renders an invisible box —
  indistinguishable from the empty state it exists to prevent. Look at it, don't assume.
- **API side:** never return a shape where "degraded / not readable / not asked" is
  indistinguishable from "empty". Return an explicit availability flag plus a reason.
