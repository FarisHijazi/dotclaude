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


LOCATE = ("_claude_roots", "claude-session-locate", "_claude_resume_id", "_claude_resume_cd")


def transcript(home, cwd, sid=SID, root=".claude"):
    slug = "".join(c if c.isalnum() else "-" for c in str(cwd))
    path = home / root / "projects" / slug / f"{sid}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'{{"cwd":"{cwd}/sub","x":1}}\n{{"cwd":"{cwd}","sessionId":"{sid}"}}\n')
    return path


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
    transcript(tmp_path, tmp_path)
    output = tmp_path / "argv"
    result = run_shell(
        tmp_path, shell,
        "claude-accounts() { :; }\n"
        "ps() { :; }\n"
        '_tagent() { printf "%s\\n" "$TCC_DETACH" "$TCC_SID" "$PWD" "$@" > "$OUTPUT"; }\n'
        + functions("_claude_argv", *LOCATE, "tcc", "tmux-restore")
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
    transcript(tmp_path, tmp_path)
    result = run_shell(
        tmp_path, shell,
        functions("_claude_argv", *LOCATE, "tcc")
        + f'\ncd "{tmp_path}"\n'
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
    transcript(tmp_path, tmp_path)
    result = run_shell(
        tmp_path, shell,
        "ps() { :; }\ntcc() { return 127; }\n"
        + functions(*LOCATE, "tmux-restore")
        + '\ntmux-restore -f "$1"\n', str(snapshot),
    )
    assert result.returncode == 127
    assert "started" not in result.stdout


def resume_script(tmp_path, call):
    return (
        "claude-accounts() { printf '%s\\n' \"$PWD\" \"$@\"; }\n"
        + functions("_claude_argv", *LOCATE, "cc")
        + f'\ncd "{tmp_path}"\n{call}\n'
    )


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize("root", [".claude", ".local/state/claude-codex/account-router/accounts/work/claude"])
@pytest.mark.parametrize("flag", ["-r", "--resume"])
def test_cc_resume_cds_to_recorded_cwd_in_any_config_dir(tmp_path, shell, root, flag):
    project = tmp_path / "proj.d" / "app"
    (project / "sub").mkdir(parents=True)
    transcript(tmp_path, project, root=root)
    result = run_shell(tmp_path, shell, resume_script(tmp_path, f"cc {flag} {SID}; echo after=$PWD"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        str(project), "--", "--dangerously-skip-permissions", flag, SID, f"after={tmp_path}",
    ]
    assert f"resuming {SID} in {project}" in result.stderr


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_cc_resume_fails_loudly_when_transcript_missing(tmp_path, shell):
    result = run_shell(tmp_path, shell, resume_script(tmp_path, f"cc -r {SID}"))
    assert result.returncode == 1
    assert not result.stdout
    assert f"no transcript {SID}.jsonl" in result.stderr


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_cc_resume_fails_when_recorded_dir_is_gone(tmp_path, shell):
    transcript(tmp_path, tmp_path / "gone")
    result = run_shell(tmp_path, shell, resume_script(tmp_path, f"cc -r {SID}"))
    assert result.returncode == 1
    assert "does not exist here" in result.stderr


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_restore_uses_transcript_cwd_and_skips_missing(tmp_path, shell):
    other = "11111111-2222-3333-4444-555555555555"
    project = tmp_path / "real"
    project.mkdir()
    transcript(tmp_path, project)
    (tmp_path / ".tmux" / "resurrect").mkdir(parents=True)
    snapshot = tmp_path / "snap.txt"
    rows = [
        ["pane", "moved", "1", ":w", "1", ":*", "0", f":{tmp_path}", "1", "claude", f":claude --session-id {SID}"],
        ["pane", "lost", "1", ":w", "1", ":*", "0", f":{tmp_path}", "1", "claude", f":claude -r {other}"],
        ["pane", "bare", "1", ":w", "1", ":*", "0", f":{project}", "1", "claude", ":claude -c"],
        ["pane", "named", "1", ":w", "1", ":*", "0", f":{project}", "1", "claude", ":claude -r nosuch"],
    ]
    (project / "decoy-file").write_text("")
    snapshot.write_text("".join("\t".join(r) + "\n" for r in rows))
    result = run_shell(
        tmp_path, shell,
        "ps() { :; }\ntcc() { echo \"tcc $PWD $*\" >> \"$OUT\"; }\n"
        + functions(*LOCATE, "tmux-restore")
        + f'\nOUT="$1"\ncd "{project}"\ntmux-restore -f "$2"\n', str(tmp_path / "calls"), str(snapshot),
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert (tmp_path / "calls").exists(), result.stdout + result.stderr
    calls = (tmp_path / "calls").read_text().splitlines()
    assert len(calls) == 2  # "moved", and "bare" -c pinned to the newest transcript there
    assert all(c.startswith(f"tcc {project} -r {SID}") for c in calls)
    assert "x lost" in result.stderr and "x named" in result.stderr
    assert "decoy" not in result.stdout + result.stderr
