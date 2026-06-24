#!/usr/bin/env python3
"""Find prior Claude Code conversations that overlap with the current task.

Scans every session JSONL under ~/.claude/projects/<encoded-cwd>/*.jsonl,
runs one or more case-insensitive regex queries across user + assistant
text, and ranks sessions by how strongly they overlap with the queries.

Output is markdown — designed to be read back by Claude so it can summarize
overlapping prior work to the user before they redo it.

Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import secrets
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
PROJECTS_DIR = CLAUDE_DIR / "projects"
SESSIONS_DIR = CLAUDE_DIR / "sessions"  # ~/.claude/sessions/<PID>.json — running-process registry

# Cap per-line text length so a huge tool_result blob doesn't blow up output.
MAX_LINE_CHARS = 400


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Match:
    line_no: int          # 1-based index into the session's flat text
    role: str             # USER | ASSISTANT | TOOL_RESULT
    timestamp: str        # ISO timestamp or ""
    text: str             # the matched line (already truncated)
    query_idx: int        # which query (0-based) matched


@dataclass
class SessionResult:
    session_file: Path
    project_dir: Path
    cwd: str                              # decoded working dir (best-effort)
    mtime: float
    lines: list[tuple[str, str, str]]     # (role, ts, text) — for context lookup
    matches: list[Match] = field(default_factory=list)
    hits_per_query: dict[int, int] = field(default_factory=dict)
    running: bool = False                 # currently-live claude process owns this session
    running_pid: int | None = None
    running_status: str | None = None     # e.g. "idle", "busy"

    @property
    def queries_hit(self) -> int:
        return sum(1 for c in self.hits_per_query.values() if c > 0)

    @property
    def total_hits(self) -> int:
        return sum(self.hits_per_query.values())

    def score(self, num_queries: int) -> int:
        # Sessions that hit MORE distinct queries are massively preferred.
        # Then by raw hit count, then by recency. Running sessions get a small nudge.
        days_old = max(0, (time.time() - self.mtime) / 86400)
        recency_bonus = max(0, 30 - int(days_old))
        running_bonus = 50 if self.running else 0
        # +10000 per distinct query so a multi-query hit always beats a single-query hit.
        return self.queries_hit * 10000 + min(self.total_hits, 100) * 10 + recency_bonus + running_bonus


# ---------------------------------------------------------------------------
# Path encoding helpers (must match Claude Code's scheme)
# ---------------------------------------------------------------------------


def encode_path(p: str) -> str:
    """Claude Code encodes paths by replacing '/' and '.' with '-'."""
    return str(Path(p).resolve()).replace("/", "-").replace(".", "-")


def decode_project_cwd(project_dir: Path) -> str:
    """Best-effort: read the `cwd` field from the first few JSONL lines.

    Falls back to the encoded folder name if no cwd is found.
    """
    for jsonl in project_dir.glob("*.jsonl"):
        try:
            with jsonl.open() as fh:
                for _ in range(20):
                    line = fh.readline()
                    if not line:
                        break
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict) and obj.get("cwd"):
                        return obj["cwd"]
        except OSError:
            continue
    return project_dir.name


# ---------------------------------------------------------------------------
# Running-session discovery — ~/.claude/sessions/<PID>.json + liveness check
# ---------------------------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    """True if a process with this PID is currently running."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)  # signal 0 = existence check, no side effect
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but is owned by another user — still "alive" for our purposes.
        return True
    except OSError:
        return False
    return True


@dataclass
class RunningSessionMeta:
    pid: int
    session_id: str
    cwd: str
    jsonl_path: Path
    status: str
    started_at: str


def discover_running_sessions() -> dict[Path, RunningSessionMeta]:
    """Return {jsonl_path: meta} for each live `claude` process registered under
    ~/.claude/sessions/<PID>.json. Stale entries (dead PID, missing JSONL) are skipped."""
    out: dict[Path, RunningSessionMeta] = {}
    if not SESSIONS_DIR.is_dir():
        return out
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            meta = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        pid = meta.get("pid")
        sess_id = meta.get("sessionId")
        cwd = meta.get("cwd")
        if not (isinstance(pid, int) and isinstance(sess_id, str) and isinstance(cwd, str)):
            continue
        if not _pid_alive(pid):
            continue
        jsonl = PROJECTS_DIR / encode_path(cwd) / f"{sess_id}.jsonl"
        if not jsonl.is_file():
            continue
        out[jsonl.resolve()] = RunningSessionMeta(
            pid=pid,
            session_id=sess_id,
            cwd=cwd,
            jsonl_path=jsonl,
            status=str(meta.get("status", "?")),
            started_at=str(meta.get("procStart", "")),
        )
    return out


# ---------------------------------------------------------------------------
# JSONL parsing — flatten a session into a list of (role, timestamp, text) rows
# ---------------------------------------------------------------------------


def _extract_text_blocks(content) -> list[str]:
    out: list[str] = []
    if isinstance(content, str):
        out.append(content)
        return out
    if not isinstance(content, list):
        return out
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            t = block.get("text") or ""
            if t:
                out.append(t)
        elif btype == "thinking":
            t = block.get("thinking") or ""
            if t:
                out.append(t)
        elif btype == "tool_use":
            # Surface the tool name + a short rendering of input — high-signal for "did we use X?".
            name = block.get("name", "")
            inp = block.get("input")
            try:
                inp_s = json.dumps(inp, ensure_ascii=False) if inp is not None else ""
            except (TypeError, ValueError):
                inp_s = str(inp)
            out.append(f"[tool_use {name}] {inp_s}")
        elif btype == "tool_result":
            inner = block.get("content")
            out.extend(_extract_text_blocks(inner))
    return out


def parse_session(path: Path) -> list[tuple[str, str, str]]:
    """Return list of (role, timestamp, text_line). Each text block may span
    multiple lines — we split on newlines so regex hits map to individual lines."""
    rows: list[tuple[str, str, str]] = []
    try:
        fh = path.open()
    except OSError:
        return rows
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            mtype = obj.get("type")
            if mtype not in ("user", "assistant"):
                continue
            ts = obj.get("timestamp", "")
            msg = obj.get("message") or {}
            content = msg.get("content")
            # Determine role label
            if mtype == "user":
                # Distinguish human text vs tool_result piggy-backed onto user messages.
                role = "TOOL_RESULT" if _is_tool_result_only(content) else "USER"
            else:
                role = "ASSISTANT"
            for block_text in _extract_text_blocks(content):
                for sub in block_text.splitlines():
                    sub = sub.rstrip()
                    if not sub:
                        continue
                    if len(sub) > MAX_LINE_CHARS:
                        sub = sub[:MAX_LINE_CHARS] + " ..[truncated].."
                    rows.append((role, ts, sub))
    return rows


def _is_tool_result_only(content) -> bool:
    if not isinstance(content, list):
        return False
    if not content:
        return False
    for block in content:
        if isinstance(block, dict) and block.get("type") != "tool_result":
            return False
    return True


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def compile_query(q: str) -> re.Pattern:
    """Compile a query as a case-insensitive regex.

    If the user-supplied string fails to compile as regex (e.g. they passed
    raw text with special chars), fall back to a literal match.
    """
    try:
        return re.compile(q, re.IGNORECASE)
    except re.error:
        return re.compile(re.escape(q), re.IGNORECASE)


def search_session(
    sess: SessionResult,
    patterns: list[re.Pattern],
    include_tool_results: bool,
) -> None:
    for i, (role, ts, text) in enumerate(sess.lines, start=1):
        if role == "TOOL_RESULT" and not include_tool_results:
            continue
        for q_idx, pat in enumerate(patterns):
            if pat.search(text):
                sess.matches.append(Match(line_no=i, role=role, timestamp=ts, text=text, query_idx=q_idx))
                sess.hits_per_query[q_idx] = sess.hits_per_query.get(q_idx, 0) + 1


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def project_dirs(
    repos: list[str],
    excludes: list[str],
    current_only: bool,
) -> list[Path]:
    if not PROJECTS_DIR.is_dir():
        return []
    all_dirs = [p for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    if current_only:
        cwd_encoded = encode_path(os.getcwd())
        return [p for p in all_dirs if p.name == cwd_encoded]
    out: list[Path] = []
    for p in all_dirs:
        cwd = decode_project_cwd(p)
        hay = f"{p.name}\n{cwd}"
        if repos and not any(_match(pat, hay) for pat in repos):
            continue
        if excludes and any(_match(pat, hay) for pat in excludes):
            continue
        out.append(p)
    return out


def _match(pattern: str, hay: str) -> bool:
    # Glob if it has wildcards, else substring (case-insensitive).
    if any(ch in pattern for ch in "*?["):
        return fnmatch.fnmatch(hay, pattern) or fnmatch.fnmatch(hay, f"*{pattern}*")
    return pattern.lower() in hay.lower()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def humanize_age(mtime: float) -> str:
    age_s = time.time() - mtime
    if age_s < 3600:
        return f"{int(age_s / 60)}m ago"
    if age_s < 86400:
        return f"{int(age_s / 3600)}h ago"
    if age_s < 86400 * 30:
        return f"{int(age_s / 86400)}d ago"
    if age_s < 86400 * 365:
        return f"{int(age_s / 86400 / 30)}mo ago"
    return f"{age_s / 86400 / 365:.1f}y ago"


def render_excerpt(sess: SessionResult, context: int, max_excerpts: int) -> str:
    """Pick best matched lines and render with context, in chronological order."""
    if not sess.matches:
        return ""

    # Deduplicate by line_no; prefer matches that hit more distinct queries first,
    # then earliest line so context isn't all clumped at the end.
    seen_lines: set[int] = set()
    picked: list[Match] = []
    # Sort so we pick matches that diversify queries first.
    by_query = sorted(sess.matches, key=lambda m: (m.query_idx, m.line_no))
    for m in by_query:
        if m.line_no in seen_lines:
            continue
        seen_lines.add(m.line_no)
        picked.append(m)
        if len(picked) >= max_excerpts:
            break

    # Expand to context windows, merge overlapping.
    windows: list[tuple[int, int]] = []
    for m in sorted(picked, key=lambda x: x.line_no):
        lo = max(1, m.line_no - context)
        hi = min(len(sess.lines), m.line_no + context)
        if windows and lo <= windows[-1][1] + 1:
            windows[-1] = (windows[-1][0], max(windows[-1][1], hi))
        else:
            windows.append((lo, hi))

    hit_lines = {m.line_no for m in sess.matches}
    out_lines: list[str] = []
    for i, (lo, hi) in enumerate(windows):
        if i > 0:
            out_lines.append("...")
        for ln in range(lo, hi + 1):
            role, ts, text = sess.lines[ln - 1]
            ts_short = ts[:19] if ts else ""
            marker = ">" if ln in hit_lines else " "
            out_lines.append(f"  {marker} [{role} {ts_short}] {text}")
    return "\n".join(out_lines)


def render_report(
    results: list[SessionResult],
    queries: list[str],
    repos_scanned: int,
    sessions_scanned: int,
    elapsed: float,
    limit: int,
    context: int,
    max_excerpts: int,
    running_count: int = 0,
) -> str:
    out: list[str] = []
    out.append("# Prior-work search")
    out.append("")
    out.append(f"**Queries:** {', '.join(repr(q) for q in queries)}")
    out.append(f"**Scanned:** {sessions_scanned} sessions across {repos_scanned} repo(s) in {elapsed:.2f}s")
    if running_count:
        out.append(f"**Live claude sessions auto-included:** {running_count}")
    out.append(f"**Matched:** {len(results)} session(s)")
    out.append("")
    if not results:
        out.append("_No prior sessions matched any query._")
        out.append("")
        out.append("Interpretation: there is no record of you having worked on this exact topic before — proceed.")
        return "\n".join(out)

    out.append("## Ranked overlap")
    out.append("")
    out.append("| # | Running | Repo | Session | Age | Queries hit | Total hits |")
    out.append("|---|---------|------|---------|-----|-------------|-----------|")
    for i, sess in enumerate(results[:limit], start=1):
        sid = sess.session_file.stem[:8]
        hit_summary = f"{sess.queries_hit}/{len(queries)}"
        run_marker = f"LIVE (pid {sess.running_pid}, {sess.running_status})" if sess.running else ""
        out.append(
            f"| {i} | {run_marker} | `{sess.cwd}` | `{sid}` | {humanize_age(sess.mtime)} | {hit_summary} | {sess.total_hits} |"
        )
    out.append("")

    out.append("## Details")
    out.append("")
    for i, sess in enumerate(results[:limit], start=1):
        sid = sess.session_file.stem[:8]
        per_q = ", ".join(
            f"{queries[q_idx]!r}={cnt}" for q_idx, cnt in sorted(sess.hits_per_query.items()) if cnt > 0
        )
        running_tag = " — **LIVE**" if sess.running else ""
        out.append(f"### {i}. `{sess.cwd}` — session `{sid}` ({humanize_age(sess.mtime)}){running_tag}")
        out.append("")
        out.append(f"- file: `{sess.session_file}`")
        if sess.running:
            out.append(f"- running: pid={sess.running_pid}, status={sess.running_status}")
        out.append(f"- per-query hits: {per_q}")
        out.append(f"- total hits: {sess.total_hits}")
        out.append("")
        out.append("```")
        out.append(render_excerpt(sess, context=context, max_excerpts=max_excerpts))
        out.append("```")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Tmp-dir writer — persist per-session contexts so the user can revisit them
# ---------------------------------------------------------------------------


def _slugify_repo(cwd: str) -> str:
    base = Path(cwd).name or "root"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-") or "repo"


def _slugify_topic(text: str, max_len: int = 50) -> str:
    """Turn freeform text into a short kebab-case slug for a directory name."""
    # Lowercase, drop everything that isn't alphanumeric or separator-ish, collapse runs.
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s:
        return "topic"
    # Drop short noise tokens (1-2 chars), but keep them if removing them empties the slug.
    parts = [p for p in s.split("-") if len(p) >= 3] or s.split("-")
    s = "-".join(parts)
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "topic"


def _auto_slug_from_queries(queries: list[str]) -> str:
    """Derive a human-readable slug from the search queries themselves."""
    joined = " ".join(queries)
    return _slugify_topic(joined)


def _unique_dir(base: Path, name: str) -> Path:
    """Pick `base/name`, or `base/name-2`, `base/name-3`, … on collision."""
    candidate = base / name
    if not candidate.exists():
        return candidate
    for i in range(2, 1000):
        candidate = base / f"{name}-{i}"
        if not candidate.exists():
            return candidate
    # extreme fallback so we never overwrite
    return base / f"{name}-{secrets.token_hex(3)}"


def write_tmp_contexts(
    results: list[SessionResult],
    queries: list[str],
    tmp_base: Path,
    limit: int,
    context: int,
    max_excerpts: int,
    slug: str | None,
) -> Path:
    """Write one .md per top-N session plus an INDEX.md. Returns the created dir."""
    tmp_base.mkdir(parents=True, exist_ok=True)
    chosen = _slugify_topic(slug) if slug else _auto_slug_from_queries(queries)
    out_dir = _unique_dir(tmp_base, f"reuse-{chosen}")
    out_dir.mkdir()

    top = results[:limit]

    # Per-session files
    written: list[tuple[int, SessionResult, Path]] = []
    for i, sess in enumerate(top, start=1):
        sid_short = sess.session_file.stem[:8]
        slug = _slugify_repo(sess.cwd)
        fname = f"{i:02d}_{slug}_{sid_short}.md"
        fpath = out_dir / fname

        per_q = ", ".join(
            f"`{queries[q_idx]}`={cnt}"
            for q_idx, cnt in sorted(sess.hits_per_query.items())
            if cnt > 0
        )

        lines: list[str] = []
        running_tag = " — LIVE" if sess.running else ""
        lines.append(f"# Prior session #{i}: {sess.cwd}{running_tag}")
        lines.append("")
        if sess.running:
            lines.append(f"- **Running:** YES — pid `{sess.running_pid}`, status `{sess.running_status}`")
        lines.append(f"- **Repo cwd:** `{sess.cwd}`")
        lines.append(f"- **Session ID:** `{sess.session_file.stem}`")
        lines.append(f"- **Session file:** `{sess.session_file}`")
        lines.append(f"- **Age:** {humanize_age(sess.mtime)}")
        lines.append(f"- **Last modified:** {dt.datetime.fromtimestamp(sess.mtime).isoformat(timespec='seconds')}")
        lines.append(f"- **Queries matched:** {sess.queries_hit}/{len(queries)}")
        lines.append(f"- **Per-query hits:** {per_q}")
        lines.append(f"- **Total hits:** {sess.total_hits}")
        lines.append("")
        lines.append("## Resume this session")
        lines.append("")
        lines.append("```bash")
        lines.append(f"cd {sess.cwd!r}")
        lines.append(f"claude --resume {sess.session_file.stem}")
        lines.append("```")
        lines.append("")
        lines.append("## Matched excerpts")
        lines.append("")
        lines.append("Lines prefixed with `>` are direct query matches; the rest is surrounding context.")
        lines.append("")
        lines.append("```")
        lines.append(render_excerpt(sess, context=context, max_excerpts=max_excerpts))
        lines.append("```")
        fpath.write_text("\n".join(lines))
        written.append((i, sess, fpath))

    # INDEX.md
    idx_lines: list[str] = []
    idx_lines.append("# Reuse — prior-work index")
    idx_lines.append("")
    idx_lines.append(f"**Queries:** {', '.join(repr(q) for q in queries)}")
    idx_lines.append(f"**Top {len(written)} sessions** ranked by query overlap then recency.")
    idx_lines.append("")
    idx_lines.append("| # | Running | Repo | Session | Age | Queries hit | Total hits | File |")
    idx_lines.append("|---|---------|------|---------|-----|-------------|-----------|------|")
    for i, sess, fpath in written:
        sid = sess.session_file.stem[:8]
        run_marker = f"LIVE pid {sess.running_pid}" if sess.running else ""
        idx_lines.append(
            f"| {i} | {run_marker} | `{sess.cwd}` | `{sid}` | {humanize_age(sess.mtime)} | "
            f"{sess.queries_hit}/{len(queries)} | {sess.total_hits} | "
            f"[{fpath.name}](./{fpath.name}) |"
        )
    idx_lines.append("")
    idx_lines.append("Open the per-session files for full excerpts and resume commands.")
    (out_dir / "INDEX.md").write_text("\n".join(idx_lines))

    return out_dir


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Search prior Claude Code conversations for overlapping work.",
    )
    p.add_argument("queries", nargs="+", help="One or more search queries (regex, case-insensitive).")
    p.add_argument(
        "--repos",
        action="append",
        default=[],
        metavar="PAT",
        help="Restrict to repos whose decoded path or encoded folder name matches PAT "
        "(substring match, or glob if PAT contains *?[). Repeatable. Default: all repos.",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PAT",
        help="Exclude repos matching PAT. Repeatable.",
    )
    p.add_argument(
        "--current-only",
        action="store_true",
        help="Search only the current working directory's history (overrides --repos).",
    )
    p.add_argument("--days", type=int, default=None, help="Only sessions modified within last N days.")
    p.add_argument("--limit", type=int, default=10, help="Max sessions in the report (default 10).")
    p.add_argument("--context", type=int, default=2, help="Lines of context around each excerpt (default 2).")
    p.add_argument(
        "--max-excerpts",
        type=int,
        default=5,
        help="Max excerpt windows shown per session (default 5).",
    )
    p.add_argument(
        "--include-tool-results",
        action="store_true",
        help="Search inside tool_result blocks too (default: skip, they're noisy).",
    )
    p.add_argument(
        "--no-include-running",
        action="store_true",
        help="Do NOT auto-include currently-running claude sessions in the scan. "
        "By default, every live `claude` process (detected via ~/.claude/sessions/<PID>.json + "
        "PID liveness check) is added to the scan set regardless of --repos/--exclude/--current-only, "
        "because live sessions are the most likely place for overlapping work.",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    p.add_argument(
        "--no-tmp",
        action="store_true",
        help="Do not write per-session context files to ./tmp/reuse-<rand>/.",
    )
    p.add_argument(
        "--tmp-base",
        type=str,
        default="./tmp",
        metavar="DIR",
        help="Base directory for the tmp/reuse-<rand>/ output dir (default: ./tmp).",
    )
    p.add_argument(
        "--tmp-context",
        type=int,
        default=8,
        help="Lines of context around each match in tmp files (default 8 — more than the report).",
    )
    p.add_argument(
        "--tmp-max-excerpts",
        type=int,
        default=12,
        help="Max excerpt windows per session in tmp files (default 12).",
    )
    p.add_argument(
        "--slug",
        type=str,
        default=None,
        metavar="SLUG",
        help="Human-friendly kebab-case slug for the tmp dir name (e.g. 'audio-dictation-claude-code'). "
        "When invoking from a Claude Code session, pass a short slug describing the task. "
        "If omitted, auto-derived from the queries. The dir becomes ./tmp/reuse-<slug>/ "
        "(with -2/-3/... suffix on collision).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    patterns = [compile_query(q) for q in args.queries]
    cutoff = None
    if args.days is not None:
        cutoff = time.time() - args.days * 86400

    proj_dirs = project_dirs(args.repos, args.exclude, args.current_only)

    # Running sessions are ALWAYS in-scope unless explicitly disabled. This means
    # even if the user passed --repos foo, every currently-running claude session
    # also gets searched (because it's the most likely place for live overlap).
    running_map: dict[Path, RunningSessionMeta] = (
        {} if args.no_include_running else discover_running_sessions()
    )

    # Build the canonical set of jsonl files to scan: union of (filtered project_dirs
    # globbing) + (running session jsonls). Dedupe by resolved path.
    to_scan: dict[Path, tuple[Path, str]] = {}  # jsonl -> (project_dir, cwd)
    for pdir in proj_dirs:
        cwd = decode_project_cwd(pdir)
        for jsonl in pdir.glob("*.jsonl"):
            to_scan[jsonl.resolve()] = (pdir, cwd)
    for jsonl, meta in running_map.items():
        to_scan.setdefault(jsonl, (jsonl.parent, meta.cwd))

    if not to_scan:
        print("ERROR: no sessions found to scan.", file=sys.stderr)
        return 1

    t0 = time.time()
    sessions_scanned = 0
    results: list[SessionResult] = []
    for jsonl, (pdir, cwd) in to_scan.items():
        try:
            mtime = jsonl.stat().st_mtime
        except OSError:
            continue
        running_meta = running_map.get(jsonl)
        # --days filter is bypassed for running sessions (they're inherently relevant).
        if cutoff and mtime < cutoff and not running_meta:
            continue
        sessions_scanned += 1
        lines = parse_session(jsonl)
        if not lines:
            continue
        sess = SessionResult(
            session_file=jsonl,
            project_dir=pdir,
            cwd=cwd,
            mtime=mtime,
            lines=lines,
            running=running_meta is not None,
            running_pid=running_meta.pid if running_meta else None,
            running_status=running_meta.status if running_meta else None,
        )
        search_session(sess, patterns, args.include_tool_results)
        if sess.matches:
            results.append(sess)

    results.sort(key=lambda s: s.score(len(patterns)), reverse=True)

    elapsed = time.time() - t0

    if args.json:
        payload = {
            "queries": args.queries,
            "scanned": {"repos": len(proj_dirs), "sessions": sessions_scanned, "elapsed_s": round(elapsed, 3)},
            "results": [
                {
                    "rank": i + 1,
                    "cwd": s.cwd,
                    "session_file": str(s.session_file),
                    "session_id": s.session_file.stem,
                    "mtime": s.mtime,
                    "age": humanize_age(s.mtime),
                    "running": s.running,
                    "running_pid": s.running_pid,
                    "running_status": s.running_status,
                    "queries_hit": s.queries_hit,
                    "total_hits": s.total_hits,
                    "per_query_hits": {args.queries[q]: c for q, c in s.hits_per_query.items()},
                    "matches": [
                        {"line": m.line_no, "role": m.role, "timestamp": m.timestamp, "text": m.text, "query": args.queries[m.query_idx]}
                        for m in s.matches[: args.max_excerpts * 3]
                    ],
                }
                for i, s in enumerate(results[: args.limit])
            ],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(
        render_report(
            results=results,
            queries=args.queries,
            repos_scanned=len(proj_dirs),
            sessions_scanned=sessions_scanned,
            elapsed=elapsed,
            limit=args.limit,
            context=args.context,
            max_excerpts=args.max_excerpts,
            running_count=len(running_map),
        )
    )

    if results and not args.no_tmp:
        try:
            out_dir = write_tmp_contexts(
                results=results,
                queries=args.queries,
                tmp_base=Path(args.tmp_base),
                limit=args.limit,
                context=args.tmp_context,
                max_excerpts=args.tmp_max_excerpts,
                slug=args.slug,
            )
            print("")
            print(f"## Persisted contexts")
            print("")
            print(f"Wrote {min(len(results), args.limit)} per-session context file(s) + INDEX.md to:")
            print("")
            print(f"  {out_dir}")
            print("")
            print(f"Open `{out_dir / 'INDEX.md'}` for the ranked index.")
        except OSError as e:
            print(f"\n[warn] could not write tmp contexts: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
