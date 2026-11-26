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


def ended(home, sid=SID):
    marker = home / "state" / "tcc" / "ended" / sid
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("0\n")
    os.utime(marker, (4_000_000_000, 4_000_000_000))
    return marker


def run_shell(tmp_path, shell, script, *args):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} is not installed")
    runner = tmp_path / "runner.sh"
    runner.write_text(script)
    env = dict(os.environ, HOME=str(tmp_path), XDG_STATE_HOME=str(tmp_path / "state"), TCC_RC_PREFIX="")
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
    transcript(tmp_path, tmp_path)
    if clean:
        ended(tmp_path)
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
    transcript(tmp_path, tmp_path)
    if clean:
        ended(tmp_path)
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


OTHER = "11111111-2222-3333-4444-555555555555"


def pane_row(tmp_path, command, session="chat"):
    (tmp_path / ".tmux" / "resurrect").mkdir(parents=True, exist_ok=True)
    # resurrect's real pane_format: session, window_index, window_active, :flags, pane_index, title, :path
    return "\t".join(["pane", session, "0", "1", ":*", "0", "title", f":{tmp_path}", "1", "claude", command])


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_restore_prefers_live_conversation_over_launch_id(tmp_path, shell):
    """/resume inside a pane keeps the launch id in argv; the save hook's line wins."""
    snapshot = tmp_path / "snap.txt"
    snapshot.write_text(
        pane_row(tmp_path, f":claude --session-id {SID}") + "\n"
        + f"claude_session\tchat\t0\t0\t{OTHER}\n"
    )
    transcript(tmp_path, tmp_path)
    transcript(tmp_path, tmp_path, sid=OTHER)
    result = run_shell(
        tmp_path, shell,
        "ps() { :; }\ntcc() { echo \"tcc $*\" >> \"$OUT\"; }\n"
        + functions(*LOCATE, "claude-live-sessions", "tmux-restore")
        + '\nOUT="$1"\ntmux-restore -f "$2"\n', str(tmp_path / "calls"), str(snapshot),
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "calls").read_text().split()[:3] == ["tcc", "-r", OTHER]


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_restore_skips_conversation_live_under_another_launch_id(tmp_path, shell):
    snapshot = tmp_path / "snap.txt"
    snapshot.write_text(pane_row(tmp_path, f":claude --session-id {SID}") + "\n")
    transcript(tmp_path, tmp_path)
    result = run_shell(
        tmp_path, shell,
        "ps() { :; }\ntcc() { echo called >> \"$OUT\"; }\n"
        + functions(*LOCATE, "tmux-restore")
        + f'\nclaude-live-sessions() {{ printf "%s\\t42\\n" {SID}; }}\n'
        + 'OUT="$1"\ntmux-restore -f "$2"\n', str(tmp_path / "calls"), str(snapshot),
    )
    assert result.returncode == 0, result.stderr
    assert "already running" in result.stdout
    assert not (tmp_path / "calls").exists()


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_restore_nudges_when_transcript_outlived_clean_exit_marker(tmp_path, shell):
    snapshot = tmp_path / "snap.txt"
    snapshot.write_text(pane_row(tmp_path, f":claude --session-id {SID}") + "\n")
    marker = ended(tmp_path)
    os.utime(transcript(tmp_path, tmp_path), (4_100_000_000, 4_100_000_000))
    result = run_shell(
        tmp_path, shell,
        "ps() { :; }\ntcc() { :; }\n"
        + functions(*LOCATE, "claude-live-sessions", "tmux-restore")
        + '\ntmux-restore -f "$1"\n', str(snapshot),
    )
    assert marker.exists()
    assert "exited abruptly" in result.stdout, result.stdout + result.stderr


def fake_bin(tmp_path, name, body):
    path = tmp_path / "fakebin" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)


def test_save_hook_records_outermost_live_claude_per_pane(tmp_path):
    """pane pid 100 -> router 200 -> claude 300 (in OTHER) -> nested claude 400; 500 is a stale pid file."""
    sessions = tmp_path / ".claude" / "sessions"
    sessions.mkdir(parents=True)
    for pid, sid in [(300, OTHER), (400, SID), (500, SID)]:
        (sessions / f"{pid}.json").write_text(f'{{"pid":{pid},"sessionId":"{sid}","cwd":"/x"}}')
    fake_bin(tmp_path, "tmux", 'printf "100\\tchat\\t0\\t1\\n"\n')
    fake_bin(tmp_path, "ps", """case "$*" in
*comm=*-p\ 300*|*comm=*-p\ 400*) echo claude ;;
*comm=*) echo bash ;;
*ppid=*-p\ 400*) echo 300 ;;
*ppid=*-p\ 300*) echo 200 ;;
*ppid=*-p\ 200*) echo 100 ;;
*ppid=*) echo 1 ;;
esac
""")
    snapshot = tmp_path / "snap.txt"
    snapshot.write_text("pane\tchat\n")
    hook = Path(__file__).parents[1] / "bin" / "tmux-resurrect-claude-ids"
    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{tmp_path / 'fakebin'}:{os.environ['PATH']}")
    env.pop("CLAUDE_CONFIG_DIR", None)
    result = subprocess.run([str(hook), str(snapshot)], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert snapshot.read_text().splitlines()[1:] == [f"claude_session\tchat\t0\t1\t{OTHER}"]
