# /reuse skill — built 2026-05-20 → 2026-05-26

Handoff doc. Skill lives at `~/.claude/skills/reuse/` (was briefly `avoid-rework` before rename).

## What was asked

> "create a new claude skill that searches for similar convos in other repos or in the same folder just to make sure that we're not redoing work that's already been done before"

Iterated through:

1. Initial build named `/avoid-rework`.
2. Renamed to `/reuse`. Persisted matched contexts to `./tmp/reuse-<rand>/`.
3. Replaced random hex with Claude-generated kebab-case slug (`./tmp/reuse-<slug>/`); collision suffix on re-run.
4. Always auto-include currently-running `claude` sessions in the scan, regardless of `--repos`/`--exclude`/`--current-only`/`--days` filters.

## Files

- `~/.claude/skills/reuse/SKILL.md` — frontmatter + usage doc consumed by Claude when `/reuse` is invoked.
- `~/.claude/skills/reuse/find_prior_work.py` — stdlib-only Python search engine (~600 lines).

No other files touched outside the skill dir.

## How it works (single source of truth — read this before editing)

### Inputs

- 1+ positional queries (case-insensitive regex; falls back to literal if regex fails to compile).
- Optional `--slug <kebab-case>` describing the task. Claude is expected to always pass this; auto-derived from queries if omitted.

### Scan set

Union of:

1. Project dirs matching `--repos`/`--exclude` filters (substring or glob), under `~/.claude/projects/`. `--current-only` restricts to the encoded cwd. `--days N` filters by JSONL mtime.
2. **Live sessions** — discovered by walking `~/.claude/sessions/<PID>.json` and PID-liveness-checking via `os.kill(pid, 0)`. Each live session's `sessionId` + `cwd` is resolved to its JSONL at `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`. **Always added regardless of filters**, bypasses `--days`. Disable with `--no-include-running`.

Dedupe by resolved Path.

### Parsing

`parse_session()` flattens each JSONL into `(role, timestamp, text)` rows. Captures:

- USER / ASSISTANT message text blocks
- `thinking` blocks
- `tool_use` blocks rendered as `[tool_use <name>] <json input>` (high signal for "did we use X?")
- `tool_result` blocks recursively (search opt-in via `--include-tool-results`; off by default, noisy)
- Tool-result-only user messages are tagged `TOOL_RESULT` so search/filter can distinguish them from real human input.

Each text block is split on newlines. Long lines truncated at `MAX_LINE_CHARS = 400`.

### Scoring

`SessionResult.score()` = `queries_hit * 10000 + min(total_hits, 100) * 10 + recency_bonus + running_bonus`

- queries_hit massively dominates: a session that matches 2/3 queries always outranks one that matches 1/3 with a thousand hits.
- recency_bonus = `max(0, 30 - days_old)`.
- running_bonus = 50 if live.

### Outputs

1. **stdout markdown report** with header (queries / scanned counts / live count), ranked table, per-session detail blocks with excerpts.
2. **`./tmp/reuse-<slug>/`** (default on, disable with `--no-tmp`):
   - `INDEX.md` — ranked table with Running column + links to per-session files.
   - `01_<repo-slug>_<sessid8>.md` … `NN_…md` — one per session, with metadata, a `claude --resume <session-id>` snippet, and richer excerpts (`--tmp-context 8`, `--tmp-max-excerpts 12`).
   - Collision handling: if dir exists, append `-2`/`-3`/… via `_unique_dir()`.
3. **`--json`** mode emits a parseable JSON payload instead of markdown.

### Live-session surfacing

Live sessions are tagged everywhere:

- stdout table: new `Running` column → `LIVE (pid N, status)`
- detail heading: `— **LIVE**`, body has `running: pid=…, status=…`
- INDEX.md: `Running` column with `LIVE pid N`
- per-session tmp file: heading suffix `— LIVE`, body shows `**Running:** YES — pid N, status X`
- JSON: `running`, `running_pid`, `running_status` fields

## Verification status

All the following were tested and work:

- ✅ Basic multi-query search with ranking
- ✅ `--repos`/`--exclude` substring + glob filters
- ✅ `--current-only`
- ✅ `--days N`
- ✅ `--limit`/`--context`/`--max-excerpts`
- ✅ `--json` output
- ✅ Tmp dir creation in cwd with explicit `--slug` (e.g. `./tmp/reuse-audio-dictation-claude-code/`)
- ✅ Auto-slug fallback derived from queries
- ✅ Collision suffix on re-run (`-2`, `-3`, …)
- ✅ Live-session auto-include with `--repos zzz-nonmatching` → still scanned 8 live sessions, matched 3
- ✅ `--no-include-running` correctly disables the auto-include
- ✅ Live sessions properly tagged `LIVE pid <N>` in all outputs

Performance: 302 sessions across 28 repos in ~1.2–1.6s on this machine.

## Known issues / not done

None that I'm aware of. The script is feature-complete per the four iterations of asks above.

## Loose ends from earlier in the same session

- `/handsfree` skill is **registered but not installed**. `~/.claude/skills/handsfree/SKILL.md` exists but only as a stub; the actual scripts/MCP server/hooks live at `~/projects/claude-voice-handsfree/plugins/handsfree/`. To activate, run `bash ~/projects/claude-voice-handsfree/install.sh` then restart claude. This was surfaced to the user but they did not ask to proceed. Not part of the /reuse skill — just noting in case the next session conflates the two.

## How to invoke

```bash
# Typical: Claude picks queries + slug from the user's task description
python3 ~/.claude/skills/reuse/find_prior_work.py \
  "<query 1>" "<query 2>" "<regex 3>" \
  --slug <kebab-case-task>

# Skip tmp dir
python3 ~/.claude/skills/reuse/find_prior_work.py "<q>" --no-tmp

# Disable live-include (e.g. for purely historical research)
python3 ~/.claude/skills/reuse/find_prior_work.py "<q>" --no-include-running

# Filter to one repo or current dir
python3 ~/.claude/skills/reuse/find_prior_work.py "<q>" --repos <pat>
python3 ~/.claude/skills/reuse/find_prior_work.py "<q>" --current-only
```

User-facing entry point is the slash command `/reuse <description>` which routes through `SKILL.md`.

## Key behavioral guarantees (don't regress these)

1. Live `claude` sessions are **always** scanned unless `--no-include-running` is passed. They bypass `--repos`/`--exclude`/`--current-only`/`--days`.
2. The tmp dir name is deterministic from `--slug` (with `-N` collision suffix), never random.
3. The skill instructs Claude to **synthesize** findings, not paste the raw report at the user. The raw report is for Claude's eyes; the user gets a recommendation + the tmp dir path.
4. Distinguish **overlap** (work that was already done) from **related** (adjacent context) in the response.
