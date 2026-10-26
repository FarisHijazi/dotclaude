"""Exercise the real shortcut functions without starting Claude or a proxy."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize(
    "args, forwarded",
    [
        ([], []),
        (["fix", "the", "bug"], ["--", "fix the bug"]),
        (["/resume"], ["--", "/resume"]),
        (["--resume", "saved-session"], ["--resume", "saved-session"]),
        (["--model", "gpt-6.1-sol[1m]"], ["--model", "gpt-6.1-sol[1m]"]),
        (["--add-dir", "dir one", "dir two"], ["--add-dir", "dir one", "dir two"]),
    ],
)
def test_cc_routes_arguments_through_account_launcher(tmp_path, shell, args, forwarded):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} is not installed")
    source = (Path(__file__).parents[1] / "scripts" / "claude-shell.sh").read_text()
    functions = []
    for name in ("_claude_argv", "cc"):
        match = re.search(rf"^{name}\(\) \{{\n.*?^\}}", source, re.MULTILINE | re.DOTALL)
        assert match is not None
        functions.append(match.group())
    runner = tmp_path / "shortcut.sh"
    runner.write_text(
        "claude-accounts() { printf '%s\\0' account-launcher \"$@\"; }\n"
        "claude() { printf '%s\\0' unexpected-direct-launch \"$@\"; }\n"
        + "\n".join(functions)
        + '\ncc "$@"\n'
    )
    result = subprocess.run(
        [executable, str(runner), *args], capture_output=True, check=True, timeout=5
    )
    actual = result.stdout.decode().rstrip("\0").split("\0")
    assert actual == ["account-launcher", "--", "--dangerously-skip-permissions", *forwarded]


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize(
    "args, claudecode, expected",
    [
        ([], "", ["account-launcher", "--"]),
        (["-p", "say ok"], "", ["account-launcher", "--", "-p", "say ok"]),
        (["fix", "it"], "", ["account-launcher", "--", "fix", "it"]),
        (["plugin", "list"], "", ["direct", "plugin", "list"]),
        (["mcp", "list"], "", ["direct", "mcp", "list"]),
        (["update"], "", ["direct", "update"]),
        (["-p", "say ok"], "1", ["direct", "-p", "say ok"]),
    ],
)
def test_claude_routes_sessions_through_account_launcher(
    tmp_path, shell, args, claudecode, expected
):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} is not installed")
    source = (Path(__file__).parents[1] / "scripts" / "claude-shell.sh").read_text()
    match = re.search(r"^claude\(\) \{\n.*?^\}", source, re.MULTILINE | re.DOTALL)
    assert match is not None
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "claude"
    fake.write_text("#!/bin/sh\nprintf '%s\\0' direct \"$@\"\n")
    fake.chmod(0o755)
    runner = tmp_path / "shortcut.sh"
    runner.write_text(
        "claude-accounts() { printf '%s\\0' account-launcher \"$@\"; }\n"
        + match.group()
        + '\nclaude "$@"\n'
    )
    env = {"PATH": f"{bindir}:/usr/bin:/bin", "CLAUDECODE": claudecode}
    result = subprocess.run(
        [executable, str(runner), *args], capture_output=True, check=True, timeout=5, env=env
    )
    assert result.stdout.decode().rstrip("\0").split("\0") == expected
