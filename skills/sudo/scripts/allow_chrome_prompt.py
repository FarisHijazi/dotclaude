#!/usr/bin/env python3
"""Answer Claude in Chrome's "New permissions required" window by clicking it.

usage: allow_chrome_prompt.py <site> [--once] [--wait 60] [--timeout 120]

Reads the window with OCR (macOS: Hammerspoon snapshot, X11: scrot), checks it
names <site>, asks the user with a FRESH notification click (even under YOLO:
this grants Claude itself more reach, so a human decides every time), then
clicks "Always allow actions on this site", or "Allow this action" with --once.
The Chrome tool call blocks while the window is open, so start this first
(Bash run_in_background) and then make the call that triggers the prompt.
If the window closed before the user clicked (exit 2 after an approval), run
both again: the approval is reused for 2 minutes.

exit: 0 allowed | 1 declined / timed out | 2 no matching window or button | 3 usage
      5 clicked, but the window stayed open (screenshots kept)
"""

import csv
import io
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
TITLE = "Claude for Chrome"  # Chrome appends " - <profile>"
MAC = platform.system() == "Darwin"
HS = "/opt/homebrew/bin/hs"
TESSERACT = "/opt/homebrew/bin/tesseract" if MAC else "tesseract"
LABELS = {"always": "Always allow actions on this site", "once": "Allow this action"}


class Failed(Exception):
    pass


class Unconfirmed(Exception):
    pass


def run(*args):
    # stdin closed: hs -c reads it and hangs otherwise.
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=30,
                          stdin=subprocess.DEVNULL).stdout


def hs(lua):
    # hs -c prints module-loading chatter too, so the answer is tagged with "=>".
    out = run(HS, "-t", "20", "-c", "return '=>' .. tostring((function() %s end)())" % lua)
    lines = [line[2:] for line in out.splitlines() if line.startswith("=>")]
    return lines[-1] if lines else ""


# hs.window.get(id) misses the extension's window at times; Chrome's own list does not.
WIN = ("local function win(id) local c = hs.application.get('com.google.Chrome') if not c then return nil end "
       "for _, w in ipairs(c:allWindows()) do if w:id() == id then return w end end end ")


def log(message):
    print("%s %s" % (time.strftime("%H:%M:%S"), message), file=sys.stderr)


def find_window():
    """Return (window id, (x, y, w, h)) of the permission window, or None."""
    if MAC:
        found = hs(
            "local c = hs.application.get('com.google.Chrome') if not c then return '' end "
            "for _, w in ipairs(c:allWindows()) do if w:title():sub(1, %d) == '%s' then "
            "local f = w:frame() return w:id()..' '..f.x..' '..f.y..' '..f.w..' '..f.h end end return ''"
            % (len(TITLE), TITLE)
        )
        if not found:
            return None
        wid, *frame = found.split()
        return wid, tuple(float(v) for v in frame)
    try:
        wid = run("xdotool", "search", "--onlyvisible", "--name", "^" + TITLE).split()[0]
    except (subprocess.CalledProcessError, IndexError):
        return None
    geo = dict(line.split("=", 1) for line in run("xdotool", "getwindowgeometry", "--shell", wid).split())
    return wid, tuple(float(geo[k]) for k in ("X", "Y", "WIDTH", "HEIGHT"))


def snapshot(wid, path):
    if MAC:
        # Through Hammerspoon's own Screen Recording grant. The hs CLI sometimes
        # aborts after the image is written, so the fresh file is what counts.
        path.unlink(missing_ok=True)
        try:
            ok = hs(WIN + "local w = win(%s) if not w then return 'gone' end "
                    "local i = w:snapshot() if not i then return 'no image' end "
                    "i:saveToFile('%s') return 'ok'" % (wid, path))
        except subprocess.CalledProcessError:
            ok = "ok" if path.exists() else "hs failed"
        if ok != "ok" or not path.exists():
            raise Failed("window snapshot failed: " + ok)
    else:
        run("scrot", "--silent", "--overwrite", "--window", wid, str(path))
    with open(path, "rb") as f:
        width = struct.unpack(">I", f.read(24)[16:20])[0]  # PNG IHDR width
    return width


def read_button(path, site, label):
    """OCR the window; return the label's centre in image pixels, if the window names <site>."""
    tsv = run(TESSERACT, str(path), "stdout", "-l", "eng", "--psm", "11", "tsv")
    lines = {}
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
        if row["level"] == "5" and row["text"].strip():
            key = tuple(row[k] for k in ("page_num", "block_num", "par_num", "line_num"))
            lines.setdefault(key, []).append(row)
    words = lambda line: " ".join(w["text"].strip() for w in line)
    text = " ".join(words(line) for line in lines.values()).casefold()
    if site.casefold() not in text:
        raise Failed("the permission window does not name " + site)
    hits = [line for line in lines.values() if words(line).casefold().startswith(label.casefold())]
    if len(hits) != 1:
        raise Failed('no unique "%s" button' % label)
    line = hits[0]
    left = min(int(w["left"]) for w in line)
    right = max(int(w["left"]) + int(w["width"]) for w in line)
    top = min(int(w["top"]) for w in line)
    bottom = max(int(w["top"]) + int(w["height"]) for w in line)
    return (left + right) / 2, (top + bottom) / 2


def locate(site, label, shots):
    found = find_window()
    if not found:
        raise Failed("no %s permission window" % TITLE)
    wid, frame = found
    image = shots / "prompt.png"
    scale = snapshot(wid, image) / frame[2]  # image pixels per screen point (2 on Retina)
    x, y = read_button(image, site, label)
    log("found the button in window %s" % wid)
    return wid, frame, (x / scale, y / scale)


def click(wid, frame, point):
    x, y = point
    if MAC:
        return hs(
            WIN + "local w = win(%s) if not w then return 'gone' end w:focus() hs.timer.usleep(400000) "
            "local f = w:frame() if f.x ~= %r or f.y ~= %r then return 'moved' end "
            "local front = hs.window.focusedWindow() if not front or front:id() ~= w:id() then return 'not focused' end "
            "local p = hs.mouse.absolutePosition() hs.eventtap.leftClick({x = %r, y = %r}) "
            "hs.timer.usleep(150000) hs.mouse.absolutePosition(p) return 'clicked'"
            % (wid, frame[0], frame[1], frame[0] + x, frame[1] + y)
        )
    run("xdotool", "windowactivate", "--sync", wid)
    if run("xdotool", "getactivewindow").strip() != wid:
        return "not focused"
    run("xdotool", "mousemove", "--sync", "--window", wid, str(round(x)), str(round(y)))
    run("xdotool", "click", "--clearmodifiers", "1")  # XTEST: the native event Chrome accepts
    return "clicked"


def approve(site, action, timeout):
    # The Chrome window closes when its tool call times out, often before the user
    # clicks. The click is then kept for 2 minutes, so the retried call is answered
    # at once: still one human decision per site.
    script = '. "$1"; YOLO=0; GRANT_SECONDS=120; request_approval "$2" "$3" "$4" "$5"'
    env = dict(os.environ, APPROVAL_TITLE="Claude wants Chrome access to " + site)
    return subprocess.run(["bash", "-c", script, "_", str(HERE / "approve.sh"), "chrome-permission:" + site,
                           action, TITLE + " permission", str(timeout)], env=env).returncode == 0


def allow(site, mode, wait, timeout):
    label = LABELS[mode]
    shots = Path(os.environ.get("TMPDIR", "/tmp")) / "sudo" / "evidence" / time.strftime("chrome-prompt-%Y%m%d-%H%M%S")
    shots.mkdir(mode=0o700, parents=True, exist_ok=True)
    deadline = time.monotonic() + wait
    while True:  # the window opens with the tool call and renders its text a moment later
        try:
            locate(site, label, shots)
            break
        except Failed:
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)
    action = ("Always allow Claude on " if mode == "always" else "Allow Claude once on ") + site
    if not approve(site, action, timeout):
        return 1
    wid, frame, point = locate(site, label, shots)  # again: it may have moved while the user decided
    log("approved; clicking")
    result = click(wid, frame, point)
    if result != "clicked":
        raise Failed(result + "; nothing clicked")
    for _ in range(10):
        time.sleep(0.5)
        if not find_window():
            print("allowed: " + action)
            return 0
    raise Unconfirmed("clicked, but the window is still open; screenshots in %s" % shots)


def main():
    args, mode, wait, timeout, site = sys.argv[1:], "always", 60, 120, None
    try:
        while args:
            arg = args.pop(0)
            if arg == "--once":
                mode = "once"
            elif arg in ("--wait", "--timeout") and args and args[0].isdecimal():
                value = int(args.pop(0))
                wait, timeout = (value, timeout) if arg == "--wait" else (wait, value)
            elif not arg.startswith("-") and site is None:
                site = arg
            else:
                raise ValueError(arg)
        if not site:
            raise ValueError("missing <site>")
    except ValueError:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 3
    if not MAC:
        os.environ.setdefault("DISPLAY", ":0")
        os.environ.setdefault("XAUTHORITY", str(Path.home() / ".Xauthority"))
    try:
        return allow(site, mode, wait, timeout)
    except Unconfirmed as error:
        print(error, file=sys.stderr)
        return 5
    except (Failed, OSError, subprocess.SubprocessError, KeyError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
