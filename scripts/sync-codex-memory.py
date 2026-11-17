#!/usr/bin/env python3
"""Mirror Claude's global memory into Codex, never in the other direction."""

import argparse
import fcntl
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import sys


LABEL = "local.claude-memory-sync"


def memory_paths(home):
    home = home.expanduser().resolve(strict=True)
    source = home / ".claude" / "memory"
    target = home / ".codex" / "memory"
    for path in (source, target):
        for ancestor in (path.parent, path):
            if ancestor.is_symlink():
                raise ValueError(f"refusing symlink: {ancestor}")
            if ancestor.exists() and not ancestor.is_dir():
                raise ValueError(f"expected directory: {ancestor}")
        if path.exists():
            for directory, directories, files in os.walk(path):
                for name in directories + files:
                    item = Path(directory) / name
                    mode = item.lstat().st_mode
                    if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                        raise ValueError(f"refusing symlink or special file: {item}")
                    if stat.S_ISREG(mode) and item.stat().st_nlink > 1:
                        raise ValueError(f"refusing hard-linked file: {item}")
    index = source / "MEMORY.md"
    if not index.is_file() or not index.read_text().strip():
        raise ValueError(f"source index is missing or empty: {index}")
    return source, target


def sync(home, dry_run=False):
    source, target = memory_paths(home)
    rsync = shutil.which("rsync")
    if not rsync:
        raise ValueError("rsync is required")
    command = [
        rsync,
        "--archive",
        "--checksum",
        "--delete-after",
        "--itemize-changes",
        "--no-owner",
        "--no-group",
    ]
    if dry_run:
        command.append("--dry-run")
    else:
        target.mkdir(parents=True, exist_ok=True)
    command.extend(["--", str(source) + "/", str(target) + "/"])
    return subprocess.run(command, check=True, timeout=60).returncode


def launch_agent(home):
    source, _ = memory_paths(home)
    state = home / ".claude" / "state"
    return {
        "Label": LABEL,
        "ProgramArguments": [
            str(Path(sys.executable).resolve()),
            str(Path(__file__).resolve()),
            "--home",
            str(home),
        ],
        "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"},
        "RunAtLoad": True,
        "WatchPaths": [str(source)],
        "StartInterval": 30,
        "ThrottleInterval": 5,
        "Umask": 0o077,
        "StandardOutPath": str(state / "memory-sync.log"),
        "StandardErrorPath": str(state / "memory-sync.log"),
    }


def install_launch_agent(home):
    if sys.platform != "darwin":
        raise ValueError("launchd installation is macOS-only; schedule this script on other systems")
    agent = launch_agent(home)
    directory = home / "Library" / "LaunchAgents"
    directory.mkdir(parents=True, exist_ok=True)
    (home / ".claude" / "state").mkdir(exist_ok=True)
    path = directory / f"{LABEL}.plist"
    path.write_bytes(plistlib.dumps(agent))
    path.chmod(0o600)
    subprocess.run(["/usr/bin/plutil", "-lint", str(path)], check=True)
    domain = f"gui/{os.getuid()}"
    present = subprocess.run(
        ["/bin/launchctl", "print", f"{domain}/{LABEL}"], capture_output=True
    ).returncode == 0
    if present:
        subprocess.run(["/bin/launchctl", "bootout", f"{domain}/{LABEL}"], check=True)
    subprocess.run(["/bin/launchctl", "bootstrap", domain, str(path)], check=True)
    print(f"Installed {path}; Claude → Codex on source changes, with a 30-second check.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home(), help="home containing .claude and .codex")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="list copies and deletions without writing")
    mode.add_argument("--install-launch-agent", action="store_true", help="install and start macOS automatic sync")
    args = parser.parse_args()
    try:
        home = args.home.expanduser().resolve(strict=True)
        if args.install_launch_agent:
            install_launch_agent(home)
        elif args.dry_run:
            return sync(home, dry_run=True)
        else:
            memory_paths(home)
            lock = home / ".claude" / ".memory-sync.lock"
            descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "w") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                return sync(home)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"memory sync failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
