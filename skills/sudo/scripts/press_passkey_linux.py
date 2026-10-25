#!/usr/bin/env python3
"""Confirm one unambiguous Bitwarden authentication entry through native X11."""

import csv
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


EXTENSION = "nngceckbapebfimnlniiiahkandclblb"
INSTANCE = f"crx_{EXTENSION}"


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=15).stdout


def identity(window):
    properties = run("xprop", "-id", window, "-notype", "WM_CLASS", "WM_NAME", "WM_WINDOW_ROLE")
    values = {}
    for line in properties.splitlines():
        key, _, value = line.partition(" = ")
        values[key] = re.findall(r'"([^"\\]*)"', value)
    return (
        values.get("WM_CLASS") == [INSTANCE, "Google-chrome"]
        and values.get("WM_NAME") == ["Bitwarden"]
        and values.get("WM_WINDOW_ROLE") == ["pop-up"]
    )


def target_point(tsv, domain):
    lines = {}
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
        if row["level"] != "5" or not row["text"].strip():
            continue
        key = tuple(row[k] for k in ("page_num", "block_num", "par_num", "line_num"))
        lines.setdefault(key, []).append(row)
    lines = list(lines.values())

    def text(words):
        return " ".join(w["text"].strip() for w in words)

    def bottom(words):
        return max(int(w["top"]) + int(w["height"]) for w in words)

    headings = [line for line in lines if text(line) == "Log in with passkey?"]
    instructions = [line for line in lines if text(line) == "Choose a passkey to log in with"]
    if len(headings) != 1 or len(instructions) != 1:
        raise ValueError("no unique Bitwarden passkey authentication heading")
    if bottom(headings[0]) >= int(instructions[0][0]["top"]):
        raise ValueError("unexpected authentication layout")
    footer = [int(line[0]["top"]) for line in lines if text(line).startswith("Use your device or hardware key")]
    limit = min(footer) if footer else float("inf")
    entries = [line for line in lines if bottom(instructions[0]) < int(line[0]["top"]) < limit]
    # A passkey's relying party may be a parent of the page's host (accounts.google.com
    # uses google.com), and Bitwarden shows it under a custom item name. Try the exact
    # domain first, then each parent that still has a dot, never a bare TLD.
    labels = domain.split(".")
    for candidate in (".".join(labels[i:]) for i in range(len(labels) - 1)):
        matches = [line for line in entries if text(line).casefold() == candidate]
        if matches:
            break
    if len(matches) != 1 or min(float(w["conf"]) for w in matches[0]) < 80:
        raise ValueError("no unique high-confidence passkey entry matching the domain")
    words = matches[0]
    left = min(int(w["left"]) for w in words)
    right = max(int(w["left"]) + int(w["width"]) for w in words)
    top = min(int(w["top"]) for w in words)
    return (left + right) // 2, (top + bottom(words)) // 2


def popups():
    try:
        windows = run("xdotool", "search", "--onlyvisible", "--classname", f"^{INSTANCE}$").split()
    except subprocess.CalledProcessError as error:
        if error.returncode != 1:
            raise
        return []
    return [window for window in windows if identity(window)]


def evidence_dir():
    # Kept for the caller to inspect; private because the popup shows account names.
    directory = Path(os.environ.get("TMPDIR", "/tmp")) / "sudo" / "evidence" / time.strftime("passkey-%Y%m%d-%H%M%S")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory


def locate(domain, shots):
    """Return (window, geometry, point) for one loaded authentication popup, sending no input but focus."""
    windows = popups()
    if len(windows) != 1:
        raise ValueError("no unique Bitwarden extension popup")
    window = windows[0]
    run("xdotool", "windowactivate", "--sync", window)
    if run("xdotool", "getactivewindow").strip() != window:
        raise ValueError("Bitwarden popup did not take focus")
    geometry = run("xdotool", "getwindowgeometry", "--shell", window)

    def read_target():
        image = str(shots / "popup.png")
        run("scrot", "--silent", "--overwrite", "--window", window, image)
        return target_point(run("tesseract", image, "stdout", "-l", "eng", "--psm", "11", "tsv"), domain)

    point = read_target()
    # Bitwarden fills its list after opening; a re-render could move the matched row.
    if read_target() != point:
        raise ValueError("Bitwarden passkey list changed while reading")
    return window, geometry, point


def confirm(domain, wait=20):
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}", domain):
        raise ValueError("Linux passkey matching requires a bare domain")
    for tool in ("xdotool", "xprop", "scrot", "tesseract"):
        if not shutil.which(tool):
            raise ValueError(f"missing Linux dependency: {tool}")
    shots = evidence_dir()
    deadline = time.monotonic() + wait
    # The popup opens a moment after the page's passkey button and fills in later still.
    while True:
        try:
            window, geometry, (x, y) = locate(domain, shots)
            break
        except ValueError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)

    def check_unchanged():
        if run("xdotool", "getactivewindow").strip() != window or not identity(window):
            raise ValueError("Bitwarden popup lost focus or changed identity; sent nothing")
        if run("xdotool", "getwindowgeometry", "--shell", window) != geometry:
            raise ValueError("Bitwarden popup moved or resized; sent nothing")

    check_unchanged()
    run("xdotool", "mousemove", "--sync", "--window", window, str(x), str(y))
    check_unchanged()
    # No --window on click: XTEST produces the native event Chrome accepts.
    run("xdotool", "click", "--clearmodifiers", "1")
    print("pressed")
    # Bitwarden closes the popup once it accepts the choice; an open popup means it did not.
    for _ in range(10):
        time.sleep(1)
        if window not in popups():
            run("scrot", "--silent", "--overwrite", str(shots / "after.png"))
            print(f"popup closed; screenshots in {shots}")
            return
    raise Unconfirmed(f"popup still open after the click; screenshots in {shots}")


class Unconfirmed(Exception):
    pass


def main():
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XAUTHORITY", str(Path.home() / ".Xauthority"))
    try:
        domain, *wait = sys.argv[1:]
        if len(wait) > 1 or not all(w.isdecimal() for w in wait):
            raise ValueError("usage: press_passkey_linux.py <domain> [wait-seconds]")
        confirm(domain.casefold(), int(wait[0]) if wait else 20)
    except Unconfirmed as error:
        print(error, file=sys.stderr)
        return 5
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        # OCR and subprocess output can contain account labels. Do not echo them.
        message = str(error) if isinstance(error, ValueError) else "Linux passkey tool failed; sent no further input"
        print(message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
