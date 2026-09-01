---
name: Find who already owns it before writing a new thing
description: Apply "reuse what exists" at the SYSTEM level — before adding a second writer/listener/cache/poller for a shared resource, grep for ownership language and extend the owner instead of cloning it.
type: feedback
---

Before adding a write path, listener, cache, or poller for a shared resource, find which
service/module already owns that responsibility.

**Why:** Two PRs for the same goal — mine was +3617/−96 over 29 files, the other +1416/−54 over 9.
Every rule below is a check that costs minutes and would have avoided the big diff.

**How to apply:**
- **Grep for ownership language first.** Search the repo *and sibling repos' CLAUDE.md* for
  `owns persistence`, `the ONLY write path`, `single source of truth`, `never modify directly`,
  `is NOT written here`. A hit naming a different owner is a boundary decision: raise it in one
  sentence with `file:line` and propose the paired change in the owning service. Never settle it by
  rewording the invariant in the same diff that breaks it, and never by leaving it standing but now
  false. (Doc-updating is normally virtuous, which is exactly why it's the tell.)
- **A bug in the owner's code is a patch to send, not a licence to become a second writer.** If I'm
  writing "unlike X, this one handles Y correctly" — stop and fix X. A more-correct second writer
  fixes nothing: the buggy one still clobbers the rows, and the survivor is whichever ran last.
- **The shim test: extend the neighbouring method, never clone it.** If the existing method could be
  rewritten as a ≤3-line call into mine, I'm writing a duplicate — generalize the existing one over
  the varying parameter and reduce the old name to a back-compat shim, same PR. Any "same as X" /
  "same pattern as X" in my own docstring or PR body is a hard stop that forces this check. Unify
  only when the difference reduces to DATA; if they differ by invariant, locking or failure
  semantics, they are genuinely separate.
- **Generalize on the axis I can enumerate** — my own schema (config fields, states, columns), not
  someone else's open-ended surface (a vendor's endpoints/verbs). Tell that I picked wrong: the
  generic layer needs a *heuristic* to classify values I don't own. For one applier over N
  heterogeneous fields, make per-field policy a frozen data table, adding a column only when I can
  name the bug omitting it causes. Reject what can't be applied live explicitly — silently dropping
  a change while returning success is worse than not offering it.
- **A named mechanism in the request is an outcome, not a mandate to own it.** "persist it", "then
  re-dispatch" describe a result; they don't authorise owning another service's table or actuating
  off a passive path. The owner is usually written down one screen from where I'm typing.
- **Never let a passive path command a live system.** A config write, health check or telemetry tick
  may only actuate through the same gate as the real command path. Tell that it doesn't: I'm
  re-deriving an operating point or re-implementing safety reasoning that path owns. Return the
  violated condition instead — per item, with measured values, in both the return value and a log
  line — and name what will and won't otherwise catch it.
- **A by-name passthrough voids every name-keyed guard above it.** `call_api(name, **params)`, raw
  SQL under an ORM, `POST /rpc {method}`: guards on the typed wrappers were keyed on names the proxy
  stopped using. Route raw and typed entry points through ONE shared predicate over the *underlying
  transport calls*, refuse where classification is ambiguous, and if a registry drives the hatch make
  the policy a required field per entry so a new entry can't default to ungated.

**Don't over-apply:** ownership language is a prompt to ASK, never a veto — don't stall or refuse
ordinary work over it. Smaller is not automatically safer; choose on named tradeoffs, not diff size.
When shipping leaner than asked, call out dropped **actuation** separately from dropped features: a
returned diagnostic (`out_of_range`, `diverged`) leaves the system in the bad state until a human
acts, so name who corrects it — and if the answer is "an existing reconcile loop", verify that loop
actually observes the quantity violated. Related: [[feedback_refactoring_discipline]].
