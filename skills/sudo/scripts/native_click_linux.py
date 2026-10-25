#!/usr/bin/env python3
"""Click caller-verified login coordinates in one explicitly selected Chrome window."""

import os
from pathlib import Path
import re
import subprocess
import sys
import time


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=10).stdout


class Unconfirmed(Exception):
    pass


def evidence_dir():
    directory = Path(os.environ.get("TMPDIR", "/tmp")) / "sudo" / "evidence" / time.strftime("click-%Y%m%d-%H%M%S")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory


def shot(window, path):
    run("scrot", "--silent", "--overwrite", "--window", window, str(path))
    return Path(path).read_bytes()


def click(window, title, coordinates, wait=10):
    if not window.isdecimal() or not title or not re.fullmatch(r"\d+,\d+", coordinates):
        raise ValueError("native click needs a numeric --window-id, --title and --click X,Y")
    x, y = map(int, coordinates.split(","))

    def check_target():
        properties = run("xprop", "-id", window, "-notype", "WM_CLASS")
        if re.findall(r'"([^"\\]*)"', properties) != ["google-chrome", "Google-chrome"]:
            raise ValueError("target is not a Chrome browser window")
        if not run("xdotool", "getwindowname", window).startswith(title):
            raise ValueError("Chrome window title no longer matches; sent nothing")

    check_target()
    geometry = run("xdotool", "getwindowgeometry", "--shell", window)
    size = dict(line.split("=", 1) for line in geometry.splitlines() if "=" in line)
    if not (x < int(size["WIDTH"]) and y < int(size["HEIGHT"])):
        raise ValueError("click coordinates are outside the Chrome window")
    run("xdotool", "windowactivate", "--sync", window)

    def check_focus():
        check_target()
        if run("xdotool", "getactivewindow").strip() != window:
            raise ValueError("Chrome window lost focus; sent nothing")
        if run("xdotool", "getwindowgeometry", "--shell", window) != geometry:
            raise ValueError("Chrome window moved or resized; sent nothing")

    check_focus()
    run("xdotool", "mousemove", "--sync", "--window", window, str(x), str(y))
    check_focus()
    shots = evidence_dir()
    # Taken after the pointer moved, so a hover highlight alone never counts as a change.
    before = shot(window, shots / "before.png")
    check_focus()
    # XTEST clicks the focused native window, unlike synthetic CDP extension events.
    run("xdotool", "click", "--clearmodifiers", "1")
    print("clicked")
    for _ in range(wait):
        time.sleep(1)
        try:
            if shot(window, shots / "after.png") != before:
                print(f"window changed; screenshots in {shots}")
                return
        except subprocess.CalledProcessError:
            print(f"window closed after the click; screenshots in {shots}")
            return
    raise Unconfirmed(f"nothing changed {wait}s after the click; screenshots in {shots}")


def main():
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XAUTHORITY", str(Path.home() / ".Xauthority"))
    try:
        if len(sys.argv) != 4:
            raise ValueError("usage: native_click_linux.py <window-id> <title-prefix> <X,Y>")
        click(*sys.argv[1:])
    except Unconfirmed as error:
        print(error, file=sys.stderr)
        return 5
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error) if isinstance(error, ValueError) else "native click failed; sent no further input", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
