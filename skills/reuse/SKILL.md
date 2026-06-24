---
name: reuse
description: Search prior Claude Code conversations across all repos (or a filtered subset) for overlapping work, then drop the most relevant prior contexts into ./tmp/reuse-<rand>/ as standalone markdown files so the user can revisit them. Use when the user invokes `/reuse <description>`, asks "have I done this before?", "is there prior work on X?", "search my history for Y", or before kicking off a non-trivial task where there's a real chance it overlaps something already built. Goal: surface concrete overlapping work that would otherwise be redone, and persist the matching contexts as files.
---

# reuse

Searches every Claude Code session JSONL under `~/.claude/projects/<encoded-cwd>/*.jsonl` for one or more search queries, ranks sessions by overlap with the current task, and writes the top matches to `./tmp/reuse-<random>/` as standalone markdown files (one per session, plus an `INDEX.md`).

Use this **before** committing to a plan whenever there's a non-trivial chance the work has already been done — in this repo or another.

## How to run

```bash
python3 ~/.claude/skills/reuse/find_prior_work.py <query> [<query>...] --slug <task-slug> [flags]
```

Always pass **multiple complementary queries** describing the task from different angles. The ranker rewards sessions that match many distinct queries, so diverse queries surface overlap that a single phrase would miss.

### Slug — name the tmp dir like a human

Always pass `--slug <kebab-case-name>` describing what you're searching for. The tmp dir is named `./tmp/reuse-<slug>/`, so a good slug makes it instantly recognizable later.

- 3–5 words, kebab-case, lowercase, alphanumeric only
- Describe the **task or topic** (not the queries themselves)
- Examples:
  - User says "audio and dictation with claude code" → `--slug audio-dictation-claude-code`
  - User says "find prior work on the auth middleware rewrite" → `--slug auth-middleware-rewrite`
  - User says "did I build a kafka consumer somewhere?" → `--slug kafka-consumer`

If `--slug` is omitted, the script auto-derives one from the queries. Prefer to pass one explicitly — your slug will be cleaner than the auto-derived one. Collisions get a `-2`/`-3`/… suffix appended.

### Query construction strategy

From the user's task description, derive 3–6 queries covering:
1. **Concrete artifact names** the prior work would mention (file names, function names, library names, command flags).
2. **The problem in the user's words** (paraphrase what they're trying to achieve).
3. **The mechanism / approach** likely used (e.g. "BM25 ranking", "websocket reconnect", "JSONL stream").
4. **A regex over a code pattern** the prior work would touch (queries are case-insensitive regex; literal strings work too).

Example — user says "add fuzzy search to the dashboard":
```bash
python3 ~/.claude/skills/reuse/find_prior_work.py \
  "fuzzy search" "fzf|rapidfuzz" "dashboard.*search" "search ranking" "autocomplete"
```

### Flags

**Filtering:**
- `--repos PAT` (repeatable, default: all): only search repos whose decoded path or encoded folder name matches PAT. Substring by default; glob if PAT contains `*?[`.
- `--exclude PAT` (repeatable): drop repos matching PAT.
- `--current-only`: search only the current working directory's history.
- `--days N`: only sessions modified in the last N days. (Running sessions bypass this.)
- `--include-tool-results`: also search inside tool_result blocks (off by default — noisy).
- `--no-include-running`: disable the always-on inclusion of live claude sessions (see below).

**Live-session auto-include (on by default):**
Every currently-running `claude` process is discovered via `~/.claude/sessions/<PID>.json` + a PID liveness check, and its session JSONL is **always added to the scan set** regardless of `--repos`/`--exclude`/`--current-only`/`--days` filters. The live sessions are flagged `LIVE pid <N>` in the report and INDEX.md, and they get a small score nudge so they surface near the top when they match. Pass `--no-include-running` to disable.

**Report (stdout):**
- `--limit N` (default 10): max sessions in the report and the tmp dir.
- `--context N` (default 2): lines of context around each excerpt in the stdout report.
- `--max-excerpts N` (default 5): max excerpt windows per session in the stdout report.
- `--json`: machine-readable output instead of markdown.

**Persisted contexts (the `./tmp/reuse-<slug>/` dir):**
- `--slug SLUG`: human-friendly kebab-case name for the tmp dir (see above — always pass this).
- `--no-tmp`: disable writing context files (default: on).
- `--tmp-base DIR` (default `./tmp`): base dir under which the named sub-dir is created.
- `--tmp-context N` (default 8): lines of context per match in the tmp files (larger than the stdout report so the file is genuinely useful to read).
- `--tmp-max-excerpts N` (default 12): max excerpt windows per session in the tmp files.

### Examples

```bash
# Default — writes ./tmp/reuse-feature-flag-rollout/ with top-10 contexts
python3 ~/.claude/skills/reuse/find_prior_work.py "feature flag" "rollout" \
  --slug feature-flag-rollout

# Only repos with "dema" in the path, last 90 days
python3 ~/.claude/skills/reuse/find_prior_work.py "modbus retry" "tcp reconnect" \
  --slug modbus-tcp-reconnect --repos dema --days 90

# Just this repo's history
python3 ~/.claude/skills/reuse/find_prior_work.py "extract_user_messages" \
  --slug extract-user-messages --current-only

# Exclude .claude config repo (skill-development noise) when looking for real product work
python3 ~/.claude/skills/reuse/find_prior_work.py "auth middleware" \
  --slug auth-middleware --exclude .claude

# Skip the tmp-dir output (just print the report)
python3 ~/.claude/skills/reuse/find_prior_work.py "kafka consumer" --no-tmp
```

## Output

### stdout — markdown report
1. **A ranked table** — sessions ordered by `queries_hit` first, then `total_hits`, then recency.
2. **Per-session excerpts** — best matched lines with `--context` lines of surrounding context. Matched lines are prefixed with `>`.
3. **Tmp-dir path** — at the bottom, the path to the persisted-contexts dir.

Sessions that hit **more distinct queries** are massively preferred — those are the ones most likely to be true overlap, not coincidental hits on a single keyword.

### `./tmp/reuse-<slug>/` — persisted contexts
- `INDEX.md` — ranked summary table linking to each per-session file.
- `01_<repo-slug>_<sess-id-short>.md` … `NN_…md` — one file per matched session, with:
  - repo + session id + age + per-query hit counts
  - a `claude --resume <session-id>` snippet so the user can jump back in
  - a generous excerpt (`--tmp-context` lines, up to `--tmp-max-excerpts` windows)

These files are **for the user to read directly** — the path is the deliverable.

## How to respond to the user

After running the script:

1. **Lead with the headline finding.** If there's clear overlap, name it in one sentence: "You already built X in `<repo>` 3 weeks ago — session `<id>`."
2. **Distinguish overlap vs. related work.**
   - **Overlap** = the prior session already did (some of) what we're about to do. Call this out loudly with the session reference and a one-line summary of what was done.
   - **Related** = adjacent context that might inform the approach but isn't a duplicate. Mention briefly.
3. **For each true overlap, summarize concretely:**
   - What was built / decided
   - Where it lives (repo path, file paths if you can infer them from the excerpts)
   - Whether it's done, abandoned, or in-progress (use timestamps + the excerpt's tone)
4. **Always show the tmp dir path** the script printed, e.g.:
   > Persisted contexts written to `./tmp/reuse-audio-dictation-claude-code/` — open `INDEX.md` for the ranked list, or jump to a specific session file.
5. **End with a recommendation:** reuse, extend, abandon-and-restart, or "this is new, proceed." If recommending reuse, include the `claude --resume <session-id>` command from the persisted file so the user can act on it immediately.

**Do not paste the raw markdown report back at the user.** Synthesize it. The report is for you to read; the user wants the conclusion plus the dir path.

If the script reports `_No prior sessions matched any query._`, say so plainly, mention no tmp dir was created, and proceed.

## When NOT to use this skill

- Trivial tasks (one-line fix, rename, typo) — overhead exceeds value.
- The user has already explicitly said "I know I've never done this before."
- You're mid-execution on a task that's already scoped — searching prior work won't change the plan now.

## Notes

- The `./tmp/` directory is created in the **current working directory** (per the user's `CLAUDE.md` convention that throwaway scratch goes under `./tmp/`). If `./tmp/` isn't gitignored in this repo, the user may want to add it.
- Each invocation creates a new `reuse-<slug>/` subdir. If you re-run with the same slug, a `-2`/`-3`/… suffix is appended so prior runs are never overwritten.
