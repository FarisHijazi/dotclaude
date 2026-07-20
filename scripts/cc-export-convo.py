#!/usr/bin/env python3
"""Export the full Claude Code conversation to a Markdown file in the project dir.

Registered as a `Stop` hook (see ~/.claude/settings.json), so it runs after every
turn and keeps the file current. Reads the hook event JSON from stdin
(`session_id`, `cwd`, `transcript_path`). Falls back to positional args
`<transcript_path> <session_id> <output_dir>` for manual runs / testing.

Writes to `<cwd>/.cc-convos/<name>-<id>-<start-yymmddhhmmss>.md`. The filename is
stable per session, so each turn overwrites the same file rather than piling up.

Disable with:  touch ~/.claude/disable_convo_export

Standalone, pure stdlib. Renders user prompts, assistant text, thinking
(collapsed), tool calls, and (truncated) tool results in transcript order.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_RESULT_MAX = 4000  # chars per tool result before truncation
TOOL_INPUT_MAX = 2000   # chars per tool_use input before truncation
DISABLE_FLAG = Path.home() / ".claude" / "disable_convo_export"


def load_entries(transcript: Path) -> list[dict]:
    out = []
    for line in transcript.read_text(errors="replace").split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def session_name(entries: list[dict], fallback: str) -> str:
    """Cascade: /rename customTitle → auto aiTitle → fallback (project dir)."""
    custom = ai = None
    for e in entries:
        t = e.get("type")
        if t == "custom-title" and e.get("customTitle"):
            custom = e["customTitle"]
        elif t == "ai-title" and e.get("aiTitle"):
            ai = e["aiTitle"]
    return custom or ai or fallback


def first_timestamp(entries: list[dict]) -> datetime:
    for e in entries:
        ts = e.get("timestamp")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
            except ValueError:
                pass
    return datetime.now(timezone.utc).astimezone()


def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return (s or "convo")[:60]


def as_text_blocks(content) -> list:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return content if isinstance(content, list) else []


def truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n… [truncated {len(s) - limit} chars]"


def render_tool_result(content) -> str:
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "image":
                    parts.append("[image]")
            else:
                parts.append(str(b))
        text = "\n".join(parts)
    else:
        text = json.dumps(content, ensure_ascii=False)
    return truncate(text.rstrip(), TOOL_RESULT_MAX)


def render(entries: list[dict]) -> list[str]:
    md: list[str] = []
    for e in entries:
        etype = e.get("type")
        if etype not in ("user", "assistant"):
            continue
        msg = e.get("message") or {}
        role = msg.get("role")
        sc = " · subagent" if e.get("isSidechain") else ""
        blocks = as_text_blocks(msg.get("content"))

        if role == "user":
            texts, results = [], []
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_result":
                    results.append(b)
                elif b.get("type") == "text":
                    texts.append(b.get("text", ""))
            joined = "\n".join(t for t in texts if t).strip()
            if joined:
                md.append(f"### 👤 User{sc}\n\n{joined}\n")
            for r in results:
                body = render_tool_result(r.get("content", ""))
                md.append(
                    f"<details><summary>🔧 tool result{sc}</summary>\n\n"
                    f"```\n{body}\n```\n\n</details>\n"
                )
        elif role == "assistant":
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "text" and b.get("text", "").strip():
                    md.append(f"### 🤖 Assistant{sc}\n\n{b['text'].strip()}\n")
                elif bt == "thinking" and b.get("thinking", "").strip():
                    md.append(
                        f"<details><summary>💭 thinking{sc}</summary>\n\n"
                        f"{b['thinking'].strip()}\n\n</details>\n"
                    )
                elif bt == "tool_use":
                    inp = json.dumps(b.get("input", {}), ensure_ascii=False, indent=2)
                    md.append(
                        f"<details><summary>🛠️ {b.get('name', '?')}{sc}</summary>\n\n"
                        f"```json\n{truncate(inp, TOOL_INPUT_MAX)}\n```\n\n</details>\n"
                    )
    return md


def resolve_inputs() -> tuple[Path, str, Path] | None:
    """Prefer hook JSON on stdin; fall back to positional args for manual runs."""
    transcript = session_id = out_dir = None
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data.strip():
            try:
                j = json.loads(data)
                transcript = j.get("transcript_path")
                session_id = j.get("session_id")
                out_dir = j.get("cwd") or os.getcwd()
            except json.JSONDecodeError:
                pass
    if not transcript and len(sys.argv) >= 4:
        transcript, session_id, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    if not transcript:
        return None
    return Path(transcript), (session_id or "session"), Path(out_dir or os.getcwd())


def main() -> int:
    if DISABLE_FLAG.exists():
        return 0
    resolved = resolve_inputs()
    if not resolved:
        # No transcript available — nothing to do (silent; hooks fire on many events).
        return 0
    transcript, session_id, out_dir = resolved
    if not transcript.is_file():
        return 0

    entries = load_entries(transcript)
    if not entries:
        return 0

    name = session_name(entries, out_dir.name)
    started = first_timestamp(entries)
    stamp = started.strftime("%y%m%d%H%M%S")
    fname = f"{slugify(name)}-{session_id}-{stamp}.md"
    out_file = out_dir / ".cc-convos" / fname

    header = [
        f"# {name}",
        "",
        f"- **Session ID:** `{session_id}`",
        f"- **Started:** {started.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- **Project:** `{out_dir}`",
        f"- **Exported:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "",
        "---",
        "",
    ]
    body = render(entries)
    try:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text("\n".join(header + body) + "\n")
    except OSError as e:
        print(f"cc-export-convo: {e}", file=sys.stderr)
        return 1
    print(str(out_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
