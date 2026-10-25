"""Run real restore/tcc functions with stub launchers, never a live tmux server."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


SID = "01234567-89ab-cdef-0123-456789abcdef"


def functions(*names):
    source = (Path(__file__).parents[1] / "scripts" / "claude-shell.sh").read_text()
    return "\n".join(
        re.search(rf"^{name}\(\) \{{\n.*?^\}}", source, re.MULTILINE | re.DOTALL).group()
        for name in names
    )


def run_shell(tmp_path, shell, script, *args):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} is not installed")
    runner = tmp_path / "runner.sh"
    runner.write_text(script)
    env = dict(os.environ, HOME=str(tmp_path), XDG_STATE_HOME=str(tmp_path / "state"))
    for name in ("TCC_PLAIN", "TCC_MAIN_ACCOUNT", "TCC_PRIVATE", "TMUX_RESTORE_EXCLUDE"):
        env.pop(name, None)
    return subprocess.run(
        [executable, str(runner), *args], env=env, capture_output=True, text=True, timeout=10
    )


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize("clean", [True, False])
@pytest.mark.parametrize("saved_command", [
    f":claude --session-id {SID}",
    f":python3 /opt/router/claude-account-router --via https://proxy.invalid -- --session-id {SID}",
])
def test_restore_routes_native_and_router_snapshots_through_launcher(
    tmp_path, shell, clean, saved_command
):
    snapshot_dir = tmp_path / ".tmux" / "resurrect"
    snapshot_dir.mkdir(parents=True)
    snapshot = snapshot_dir / "tmux_resurrect_20261025T000000.txt"
    snapshot.write_text("\t".join([
        "pane", "saved-chat", "1", ":window", "1", ":*", "0", f":{tmp_path}",
        "1", "claude", saved_command,
    ]) + "\n")
    if clean:
        marker = tmp_path / "state" / "tcc" / "ended" / SID
        marker.parent.mkdir(parents=True)
        marker.write_text("0\n")
    output = tmp_path / "argv"
    result = run_shell(
        tmp_path, shell,
        "claude-accounts() { :; }\n"
        "ps() { :; }\n"
        '_tagent() { printf "%s\\n" "$TCC_DETACH" "$TCC_SID" "$PWD" "$@" > "$OUTPUT"; }\n'
        + functions("_claude_argv", "tcc", "tmux-restore")
        + '\nOUTPUT="$1"\ntmux-restore -f "$2"\n',
        str(output), str(snapshot),
    )
    assert result.returncode == 0, result.stderr
    argv = output.read_text().splitlines()
    expected = [
        "1", SID, str(tmp_path), "tcc", "claude-accounts", "--", "--remote-control",
        "--dangerously-skip-permissions", "-r", SID,
    ]
    assert argv[:len(expected)] == expected
    assert (len(argv) == len(expected)) == clean
    if not clean:
        assert argv[-1].startswith("[tmux-restore]")
    assert "1 started" in result.stdout


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize("plain", [False, True])
def test_tcc_requires_launcher_unless_plain_explicit(tmp_path, shell, plain):
    result = run_shell(
        tmp_path, shell,
        functions("_claude_argv", "tcc")
        + '\n_tagent() { printf "%s\\n" "$@"; }\n'
        + 'command() { return 1; }\n'
        + ("TCC_PLAIN=1\n" if plain else "")
        + f"tcc -r {SID}\n",
    )
    if plain:
        assert result.returncode == 0
        assert result.stdout.splitlines() == ["tcc", "claude", "--dangerously-skip-permissions", "-r", SID]
    else:
        assert result.returncode == 127
        assert "refusing a direct Claude launch" in result.stderr
        assert not result.stdout


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize("clean", [True, False])
def test_restore_propagates_launcher_failure(tmp_path, shell, clean):
    snapshot_dir = tmp_path / ".tmux" / "resurrect"
    snapshot_dir.mkdir(parents=True)
    snapshot = snapshot_dir / "tmux_resurrect_20261025T000000.txt"
    snapshot.write_text("\t".join([
        "pane", "saved-chat", "1", ":window", "1", ":*", "0", f":{tmp_path}",
        "1", "claude", f":claude --session-id {SID}",
    ]) + "\n")
    if clean:
        marker = tmp_path / "state" / "tcc" / "ended" / SID
        marker.parent.mkdir(parents=True)
        marker.write_text("0\n")
    result = run_shell(
        tmp_path, shell,
        "ps() { :; }\ntcc() { return 127; }\n"
        + functions("tmux-restore")
        + '\ntmux-restore -f "$1"\n', str(snapshot),
    )
    assert result.returncode == 127
    assert "started" not in result.stdout
