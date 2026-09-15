# Brief template

The subagent has no chat history. If a constraint is not in the prompt or
discoverable in the repo, it does not exist for them.

```xml
<task>
Concrete job and where it lives. What to change; what to leave untouched.
</task>

<key_paths>
- path/a — why it matters
- path/b — pattern to follow
</key_paths>

<verification_loop>
Run before finishing and fix failures:
  <real test command>
  <real lint/typecheck command>
Confirm git status shows only intended paths.
</verification_loop>

<action_safety>
No unrelated refactors. Do NOT git add or commit — leave work uncommitted.
</action_safety>

<escape_hatch>
If anything is unclear, or you are blocked, or a required resource is missing:
output a single line starting with NEED_HELP: followed by your question, and
stop. Do not guess on ambiguous requirements; do not silently skip blocked
steps.
</escape_hatch>

<structured_output_contract>
1. What changed and why
2. Files touched
3. Gate outcomes
4. Open questions
</structured_output_contract>
```

## Rules

0. The `<escape_hatch>` block is mandatory in every brief — it is what lets the
   orchestrator distinguish "stuck, needs an answer" from "done". Headless
   agents cannot ask interactively; without it they guess.
1. One task per dispatch.
2. Copy real gate commands from the repo (`package.json`, `Makefile`, etc.).
3. For parallel writers, add an explicit file allow-list.
4. Resume/delta briefs: only the correction + what must still pass.

## Ask example

```xml
<task>
Locate every write path that updates device setpoint. Do not edit files.
</task>
<structured_output_contract>
Table: path | symbol | notes. Max ~40 lines.
</structured_output_contract>
```
