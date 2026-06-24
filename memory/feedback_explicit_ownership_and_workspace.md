---
name: explicit-ownership-and-workspace
description: Faris wants explicit ownership boundaries (AI vs human) in file organization, with a seed/draft workspace pattern for iterative work and direct writes for fire-and-forget.
metadata:
  type: feedback
---

When organizing files in any project where AI and human collaborate, make ownership and access patterns explicit and transparent. Faris thinks in terms of clear responsibilities.

**Core principles:**

1. **Every file has an owner.** State who owns it (user or AI) and what the other party can do with it (read only, read+write, never access). No ambiguous shared-ownership files without rules.

2. **Workspace pattern for iterative work:** When back-and-forth is expected, use a task-scoped directory with:
   - `seed.md` = user-owned (the idea, prompt, skeleton). AI reads but never modifies.
   - `draft.md` = AI-owned (generated from seed). Regenerable. User reads but edits a copy.
   - User updates seed, AI regenerates draft. Seed is source of truth.

3. **Direct write for fire-and-forget:** If it's a one-time write with maybe a tiny edit, write directly to the target location. Don't over-engineer with workspace/versioning for simple tasks.

4. **The deciding question: "Do I expect back-and-forth?"** Yes = workspace. No = direct write.

5. **Separate "always read" from "read on demand":** Config that shapes AI behavior = always loaded. Reference material = loaded when relevant. Task-specific outputs = loaded only when that task is active.

6. **v1/v2/v3 naming is bad** because it doesn't show ownership. `seed.md` vs `draft.md` is better because the name itself tells you who controls it.

7. **User-owned files are sacred.** `TODO.todo`, `seed.md`, `personalnotes/` = AI reads (if permitted) but NEVER writes. Ownership means the owner is the only one who modifies.

**Why:** Faris values transparency in who's responsible for what. Ambiguous ownership leads to the AI overwriting user work or the user being unsure if a file is safe to edit. Explicit boundaries eliminate that friction entirely.

**How to apply:** When setting up any project structure, define ownership per directory in CLAUDE.md. When creating a new artifact, ask: "Is this iterative (workspace) or fire-and-forget (direct write)?" When touching any file, check: "Am I the owner? If not, am I allowed to write here?"
