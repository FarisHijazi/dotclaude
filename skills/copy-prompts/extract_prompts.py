#!/usr/bin/env python3
"""Extract just the user-typed prompts from the current Claude Code session.

Standalone — no external dependencies, pure stdlib. Auto-detects the current
session JSONL by encoding the cwd the way Claude Code does. Writes the result
to a randomized temp file (path printed on stdout) and copies to the system
clipboard if a tool is available.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
PROJECTS_DIR = CLAUDE_DIR / "projects"


def encode_path(p: str) -> str:
    """Same encoding Claude Code uses for ~/.claude/projects/<encoded>/ dirs."""
    return str(Path(p).resolve()).replace("/", "-").replace(".", "-")


def find_current_session() -> Path | None:
    """Most-recently-modified .jsonl under the encoded cwd dir."""
    history_dir = PROJECTS_DIR / encode_path(os.getcwd())
    if not history_dir.is_dir():
        return None
    sessions = sorted(history_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return sessions[0] if sessions else None


def extract_user_messages(session_file: Path) -> list[str]:
    """Human-typed user messages only — skips tool_result blocks, sidechains, meta."""
    out: list[str] = []
    for line in session_file.read_text().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "user":
            continue
        if obj.get("isSidechain") or obj.get("isMeta"):
            continue
        msg = obj.get("message", {})
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        text_parts: list[str] = []
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
        text = "\n".join(p for p in text_parts if p).strip()
        if text:
            out.append(text)
    return out


def copy_to_clipboard(text: str) -> str | None:
    if sys.platform == "darwin":
        candidates = [["pbcopy"]]
    elif sys.platform == "win32":
        candidates = [["clip"]]
    else:
        candidates = [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]
    for cmd in candidates:
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            if p.returncode == 0:
                return cmd[0]
        except FileNotFoundError:
            continue
    return None


def main() -> int:
    session = find_current_session()
    if not session:
        print(
            f"ERROR: no session JSONL found for cwd={os.getcwd()}\n"
            f"  (looked under {PROJECTS_DIR / encode_path(os.getcwd())})",
            file=sys.stderr,
        )
        return 1

    messages = extract_user_messages(session)
    if not messages:
        print(f"ERROR: no human-typed messages in {session}", file=sys.stderr)
        return 1

    blob = "\n\n---\n\n".join(messages)

    tmpdir = Path(tempfile.mkdtemp(prefix="claude-copy-prompts-"))
    out_file = tmpdir / "response.md"
    out_file.write_text(blob)

    tool = copy_to_clipboard(blob)

    print(f"Copied {len(messages)} prompt(s) ({len(blob)} chars):")
    print(f"  file:      {out_file}")
    if tool:
        print(f"  clipboard: via {tool}")
    else:
        print(f"  clipboard: no tool available (tried pbcopy/clip/wl-copy/xclip/xsel)")
    print(f"  session:   {session.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
