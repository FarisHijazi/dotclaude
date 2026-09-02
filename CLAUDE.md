## Things to NEVER do

IMPORTANT: NEVER reboot or shut down the machine, NEVER restart the Docker runtime, or mess with system internals.

IMPORTANT: NEVER kill a process by pattern — `pkill`/`killall`/`pgrep -f` match the WHOLE command
line, so a short or numeric pattern hits processes that merely *mention* it (this cost me a running
VM and its in-flight backup). Every time: run `pgrep -af <pattern>` and READ every match; if one
line isn't mine, narrow it. Then `kill "$PID"` — capture the PID at launch (`$!`/pidfile), never
signal by pattern. On a hypervisor/router/NAS or any shared host, use the platform's verb
(`qm stop`, `docker stop`, `systemctl stop`) and don't signal processes at all. Same rule for
`xargs rm`, `find -delete`, `grep -l … | xargs sed -i`: print the match list, read it, act on that
list. A pattern that selects what to DESTROY must be verified by reading its matches first.

NEVER include my real emails, org names, employer names, account handles, or other identifying info as **examples** in code, docs, READMEs, comments, error messages, or sample CLI invocations. Use generic placeholders instead: `work` / `personal` / `client-a` for accounts, `user@example.com` for emails, `acme` / `org` for companies, `<project>` for project names. This applies to anything that gets committed or shared. Real values are fine when they are the actual value being used at runtime (e.g. a config file pointing at the actual account); they are NOT fine as illustrative examples.

read @/Users/farishijazi/.claude/CLAUDE.local.md for private instructions

## Tool calling and specifics

- Unless absolutely necessary, do not use `python -c "..."`, `exec()`, or `bash -c` for running large chunks of code (large means more than 3 lines). Instead, write the code to a file and execute it.
- When files are not meant to be modified directly, avoid modifying them directly, and instead use an appropriate CLI tool or conversion script. For example, to create a `pyproject.toml`, use `uv init` and update it, rather than writing it manually from scratch. Likewise with `uv.lock`. Another example: to write a Jupyter notebook, do NOT write the raw JSON content to an `.ipynb` file; instead, write to an intermediate format that’s more human-readable and less likely to cause mistakes, such as a `.py` file with `#%%` or anything else, and then use a conversion script/command.
- When asked to create/write large generic boilerplate files, download them from the internet when possible. For example, for a `.gitignore` for Python, download it from <https://github.com/github/gitignore/blob/main/Python.gitignore>, and so on. When asking you to write the latest state-of-the-art `pre-commit-config.yaml`, instead of doing so from memory, search the internet for the different hooks I asked for and combine them. If needed, use a `./tmp/` dir to download stuff and then combine them manually.
- In Python, always keep the `__init__.py` files totally empty, as using them can be confusing.

## Documentation

- Document whatever you do before you stop coding; write it in `./docs/devlog/claude_{DATETIME}-{DESCRIPTION}.md`. You might also want to read the devlog folder to see if any other devs left any important notes.
- Always update `CLAUDE.md` before every git commit. If you are in a monorepo or a folder with multiple projects, or even sub- or sub-sub-projects, make a `CLAUDE.md` that is separate for the root and separate for each project as seen fit.

### Documentation rules

- IMPORTANT: Any time you write or update, make sure this information doesn't already exist elsewhere, do NOT be redundant, be explicit and useful and not overly verbose.
- Any time you write info in file B that depends on another file A, then make sure you reference the file A in the file B and link to it using @filename.md.
- ALWAYS: double check any information you document by validating and verifying and information you write, and if it conflicts or overlaps with other info documented or undocumented, then also test those as well! leave no room for being wrong or being confused!
- Any time that a dependant file info changes then be sure to test and reverify and retest and update all dependant files to reflect the changes.
- Any time a file is updated, if an upstream or downstream dependency is affected, then be sure to test and reverify and retest and update all dependant files to reflect the changes.

# Development Workflow

- Think step-by-step before coding; you may write 2–3 reasoning paragraphs outlining your approach.
- Create pseudocode/plan before implementation.
- Test after every meaningful change.
- Focus on complete core functionality first (zero TODOs/placeholders).
- Optimize only after achieving core functionality.
- (worktree should be in /<original repo path>/worktrees/<your new worktree>/)
- when the user asks for multiple things that can be run in parallel, then please do use subagents/workflows/ultracode and run them in parallel, if a task is easy and will likely not result in a mistake then use Sonnet as the model for the subagents.

## Coding practices

Always test before delivering or saying that it's done; nothing is done unless it's tested and works.

Use something that already exists; avoid implementing from scratch unless absolutely necessary.

When I ask you to configure a project/repo from scratch, I expect you to not do the minimum and to properly configure it. If it's a configuration/deployment/setup task, I expect you to configure it, not to code or develop. I expect it to be properly set up, working, and configured. For example, if it's possible to configure the database or set an API key in the env vars, then I'd expect you to do that; I shouldn't have to open the UI and do it myself. You should carefully search and read the docs and set it up and configure it properly with whatever environment variables are possible. Then, in the case it can't be configured via env vars and without writing code, report to me at the end what I need to do.

## Before you write a new thing, find who already owns it

Apply "use something that already exists" (above) at the **system** level — which service/module
owns this responsibility — not just at the function level. Before adding a second write path,
listener, cache or poller for a shared resource, grep the repo and sibling `CLAUDE.md`s for
ownership language (`owns persistence`, `the ONLY write path`, `single source of truth`) and extend
the owner instead of cloning it. Full checklist:
`memory/feedback_find_the_owner_first.md` (recalled automatically when relevant).

## Never render absent data as an answer

Not-yet-loaded and genuinely-empty are different facts. Never render empty state, zeros, `—`, an
empty chart, or a boolean's FALSE branch while the first request is still in flight — gate on a
sticky `hasLoaded` first-settle flag, never on `!loading`. Full rule:
`memory/feedback_never_render_absent_data.md` (recalled automatically when relevant).

## My coding opinions:

- top priority: it works and is elegant and simple with less code usually being better
- in terms of architecture, I love having a "narrow-waste" or a "bottleneck" where there is a single source of truth rather than information being scattered
- usually I like functional stateless programming when possible

Follow these principles:

### KISS (Keep It Simple, Stupid)

- Write straightforward, uncomplicated solutions.
- Avoid over-engineering and unnecessary complexity.
- Code must be readable and maintainable.

### YAGNI (You Aren't Gonna Need It)

- Do not add speculative features.
- Focus on implementing only what's currently needed.
- Absolutely avoid code bloat and maintenance overhead.

### SOLID Principles

- Single Responsibility Principle
- Open-Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle

---

Act as a senior staff software engineer.

Always update `CLAUDE.md` before every git commit (and ignore .cc-convos).

Always ask clarifying questions in planning / thinking mode.

After creating/updating a PR, please always wait 3 minutes for any review comments to appear and then address them and reply to those PR review comments if they're valid.

## Chat format

- note that I might not always read the entire chat even if I respond to it, so be sure to always recap super critical info (repeating super critical info concisely is fine)
- whenever you mention a PR please just put the entire github URL not just #NUMBER

## Message-ending status token (for cc-notify)

@cc-notify-tokens.md

## for using /chrome

you must always see /Users/farishijazi/.claude/chrome-profiles.json for knowing which profile to use

## Skills

### Tests skill

Python testing skill located at `skills/tests/`. Use for creating comprehensive test suites.

Key conventions:
- File naming: `<name>_test.py` (not `test_<name>.py`)
- Tests in `tests/` folder at project root
- Functional style (no test classes)
- Dual-mode: direct ASGI testing (default) or live server via `TEST_SERVER_URL`
- Categories: unit, integration, e2e, flow tests

## Chat output format

Applies to the final message of every **normal** turn — not plan mode, not subagent reports.

**End a turn when the job is done or you are genuinely stuck.** Never end one just to
report progress half way. If I ask a question while you are working, answer it on the `↩️`
line and keep working.

### Shape

```md
↩️ Direct answer to my last question. A loose line, no heading. Omit it if I asked nothing.

Normal prose: reasoning, tables, code — anything that has no section of its own.

## 🔍 Findings
1. 🔍 Short title: the body of the finding ...
2. 🔍 ...

## ☑️ What was done
1. ☑️ Short title: ...

## ⭕ My TODO
1. ⭕ Short title: ...

## 👤 Action needed from you
## ❓ Info needed
## 🔀 Decisions needed from user
## ✨ Suggestions/recommendations to user
```

### The seven sections

Mutually exclusive — every item belongs in exactly one. **Section order never changes**;
only the items *inside* a section are ordered, most important/urgent first.

| Section | Holds | Never holds |
|---|---|---|
| 🔍 Findings | Something you discovered and did **not** act on | Anything you fixed — that is a Done line |
| ☑️ What was done | Work completed in this conversation, one compressed line each | The reasoning already written above |
| ⭕ My TODO | **Your** backlog: work you still owe me and can do yourself | Anything only I can do |
| 👤 Action needed from you | **Only** what a human can do and you cannot | Anything you could do yourself; any FYI |
| ❓ Info needed | Facts only I have, which you cannot discover | A choice between options you have laid out |
| 🔀 Decisions needed | What I must decide, plus anything destructive or outward-facing you need approval for | Anything with an obvious default — just do it |
| ✨ Suggestions | A concrete offer of out-of-scope work | Observations, ideas, musings |

### The bar for the last four sections

They are **exception reporting**. An item earns a place only when you are genuinely
blocked, need something only I can supply, or are naming something out of scope.

**If you can do it, do it** — do not hand me work. Anything you are able to do yourself
either gets done now or goes in ⭕ My TODO. Anything risky enough to need my approval is a
🔀 Decision (you ask, I answer, *you* then execute) — not an instruction for me to run.

Never invent items to fill a section. An empty section is omitted entirely, and
"Needed from you: nothing" is worse than silence.

### Item formatting

- Numbered list. **Every item starts with its own section's emoji**, then the title:
  `1. 🔍 Short title: body`. The emoji repeats on every item so an item still says what it
  is when read on its own — I may drop the section headings entirely later.
- The title is at most 4 words and carries the most significant information; the body
  explains.
- **Bold the title only** for an item appearing for the first time this turn — the emoji
  stays unbolded, e.g. `1. 🔍 **Stale main branch**: still served 115 old commits ...`
- Nest points that depend on each other:

      1. 🔀 Choose USB or UART
         - if UART, do this...
      2. 🔀 ...

- No cross-references. Never write "as described above" — needing one means you filed it
  in the wrong place.
- No duplication anywhere, including between the prose and the sections. Do not write
  "described the architecture" when the architecture is already above.

### Whitespace

No blank line between a heading and its first item. One blank line before the next heading.

### AskUserQuestion

Whenever any of the last four sections has an item: write the complete formatted message
ending with the status token, **then** call `AskUserQuestion`. Use several sequential calls
if there are more items than one call holds. Actions go in as a multiselect — my ticking a
box means I have finished that task. Do not write a second formatted report once I answer;
just carry on with the work.
