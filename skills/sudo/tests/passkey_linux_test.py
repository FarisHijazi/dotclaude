"""Run with python3 passkey_linux_test.py. No desktop input is sent."""

import csv
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


passkey = load("press_passkey_linux")
native = load("native_click_linux")
os.environ["TMPDIR"] = tempfile.mkdtemp(prefix="sudo-test-")


class FakeClock:
    """Retries and post-click checks sleep; the tests advance time instead."""

    now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    strftime = staticmethod(time.strftime)


passkey.time = native.time = FakeClock()
PROPERTIES = f'WM_CLASS = "{passkey.INSTANCE}", "Google-chrome"\nWM_NAME = "Bitwarden"\nWM_WINDOW_ROLE = "pop-up"\n'
GEOMETRY = "WINDOW=42\nX=10\nY=10\nWIDTH=500\nHEIGHT=600\nSCREEN=0\n"


def tsv(domain="example.com", heading="Log in with passkey?", duplicate=False, confidence=95, entry_top=120):
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")
    writer.writerow("level page_num block_num par_num line_num word_num left top width height conf text".split())
    lines = [(heading, 20), ("Choose a passkey to log in with", 80), (domain, entry_top)]
    if duplicate:
        lines.append((domain, 170))
    lines.append(("Use your device or hardware key", 240))
    for line, (text, top) in enumerate(lines, 1):
        for word, text in enumerate(text.split(), 1):
            writer.writerow([5, 1, line, 1, 1, word, 20 + word * 25, top, 20, 12, confidence, text])
    return output.getvalue()


def rejects(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError("unsafe input was accepted")


def test_exact_domain_is_selected():
    assert passkey.target_point(tsv(), "example.com") == (55, 126)


def test_domain_substrings_are_rejected():
    for domain in ("notexample.com", "example.com.evil.test", "user@example.com"):
        rejects(lambda: passkey.target_point(tsv(domain), "example.com"))


def test_duplicate_entries_are_rejected():
    rejects(lambda: passkey.target_point(tsv(duplicate=True), "example.com"))


def test_save_passkey_and_locked_vault_are_rejected():
    for heading in ("Save passkey", "Unlock your vault"):
        rejects(lambda: passkey.target_point(tsv(heading=heading), "example.com"))


def test_uncertain_ocr_is_rejected():
    rejects(lambda: passkey.target_point(tsv(confidence=50), "example.com"))


def passkey_commands(focus="42", properties=PROPERTIES, windows="42", moved=False, rerendered=False, stays_open=False):
    calls = []
    geometries = 0
    readings = 0
    clicked = False

    def run(*args):
        nonlocal geometries, readings, clicked
        calls.append(args)
        if args[:2] == ("xdotool", "click"):
            clicked = True
        if args[0] == "xprop":
            return properties
        if args[:2] == ("xdotool", "search"):
            return "" if clicked and not stays_open else windows
        if args[:2] == ("xdotool", "getactivewindow"):
            return focus
        if args[:2] == ("xdotool", "getwindowgeometry"):
            geometries += 1
            return GEOMETRY + ("CHANGED=1\n" if moved and geometries > 1 else "")
        if args[0] == "tesseract":
            readings += 1
            return tsv(entry_top=170 if rerendered and readings % 2 == 0 else 120)
        return ""

    return calls, run


def test_passkey_clicks_exactly_once():
    calls, run = passkey_commands()
    with patch.object(passkey, "run", run), patch.object(passkey.shutil, "which", return_value="tool"):
        passkey.confirm("example.com")
    assert [c for c in calls if c[:2] == ("xdotool", "click")] == [("xdotool", "click", "--clearmodifiers", "1")]
    assert ("xdotool", "mousemove", "--sync", "--window", "42", "55", "126") in calls


def test_passkey_popup_left_open_is_reported():
    calls, run = passkey_commands(stays_open=True)
    with patch.object(passkey, "run", run), patch.object(passkey.shutil, "which", return_value="tool"):
        try:
            passkey.confirm("example.com")
        except passkey.Unconfirmed:
            pass
        else:
            raise AssertionError("an open popup after the click was reported as success")
    assert sum(c[:2] == ("xdotool", "click") for c in calls) == 1


def test_passkey_waits_for_a_late_popup():
    calls, base_run = passkey_commands()
    searches = 0

    def run(*args):
        nonlocal searches
        if args[:2] == ("xdotool", "search"):
            searches += 1
            if searches < 4:
                calls.append(args)
                return ""
        return base_run(*args)

    with patch.object(passkey, "run", run), patch.object(passkey.shutil, "which", return_value="tool"):
        passkey.confirm("example.com")
    assert sum(c[:2] == ("xdotool", "click") for c in calls) == 1


def test_passkey_failure_sends_no_click():
    for options in ({"focus": "99"}, {"properties": PROPERTIES.replace(passkey.INSTANCE, "google-chrome")}, {"windows": "42 43"}, {"windows": ""}, {"moved": True}, {"rerendered": True}):
        calls, run = passkey_commands(**options)
        with patch.object(passkey, "run", run), patch.object(passkey.shutil, "which", return_value="tool"):
            rejects(lambda: passkey.confirm("example.com"))
        assert not any(c[:2] == ("xdotool", "click") for c in calls)


def test_invalid_domain_never_touches_desktop():
    with patch.object(passkey, "run") as run:
        rejects(lambda: passkey.confirm("example.com; anything"))
    run.assert_not_called()


def native_commands(focus="42", title="Sign in - Google", chrome=True, moved=False, changes=True):
    calls = []
    geometries = 0
    clicked = False

    def run(*args):
        nonlocal geometries, clicked
        calls.append(args)
        if args[:2] == ("xdotool", "click"):
            clicked = True
        if args[0] == "scrot":
            Path(args[-1]).write_bytes(b"after" if clicked and changes else b"before")
        if args[0] == "xprop":
            return 'WM_CLASS = "google-chrome", "Google-chrome"' if chrome else 'WM_CLASS = "terminal", "Terminal"'
        if args[:2] == ("xdotool", "getwindowname"):
            return title
        if args[:2] == ("xdotool", "getactivewindow"):
            return focus
        if args[:2] == ("xdotool", "getwindowgeometry"):
            geometries += 1
            return GEOMETRY + ("CHANGED=1\n" if moved and geometries > 1 else "")
        return ""

    return calls, run


def test_native_click_has_no_keys_or_autofill():
    calls, run = native_commands()
    with patch.object(native, "run", run):
        native.click("42", "Sign in", "100,200")
    assert [c for c in calls if c[:2] == ("xdotool", "click")] == [("xdotool", "click", "--clearmodifiers", "1")]
    assert not any(c[:2] == ("xdotool", "key") for c in calls)


def test_native_click_without_visible_change_is_reported():
    calls, run = native_commands(changes=False)
    with patch.object(native, "run", run):
        try:
            native.click("42", "Sign in", "100,200")
        except native.Unconfirmed:
            pass
        else:
            raise AssertionError("an unchanged window after the click was reported as success")
    assert sum(c[:2] == ("xdotool", "click") for c in calls) == 1


def test_native_target_failures_never_click():
    for options in ({"focus": "99"}, {"title": "Other page"}, {"chrome": False}, {"moved": True}):
        calls, run = native_commands(**options)
        with patch.object(native, "run", run):
            rejects(lambda: native.click("42", "Sign in", "100,200"))
        assert not any(c[:2] == ("xdotool", "click") for c in calls)


def test_focus_stolen_after_pointer_move_never_clicks():
    for module, action in (
        (passkey, lambda: passkey.confirm("example.com")),
        (native, lambda: native.click("42", "Sign in", "100,200")),
    ):
        calls, base_run = passkey_commands() if module is passkey else native_commands()
        moved_pointer = False

        def run(*args):
            nonlocal moved_pointer
            result = base_run(*args)
            if args[:2] == ("xdotool", "mousemove"):
                moved_pointer = True
            if args[:2] == ("xdotool", "getactivewindow") and moved_pointer:
                return "99"
            return result

        with patch.object(module, "run", run), patch.object(passkey.shutil, "which", return_value="tool"):
            rejects(action)
        assert not any(c[:2] == ("xdotool", "click") for c in calls)


def test_missing_passkey_dependency_never_touches_desktop():
    with patch.object(passkey.shutil, "which", return_value=None), patch.object(passkey, "run") as run:
        rejects(lambda: passkey.confirm("example.com"))
    run.assert_not_called()


def test_native_out_of_bounds_never_clicks():
    for coordinates in ("500,200", "20,600", "-1,20", "20,20;anything"):
        calls, run = native_commands()
        with patch.object(native, "run", run):
            rejects(lambda: native.click("42", "Sign in", coordinates))
        assert not any(c[:2] == ("xdotool", "click") for c in calls)


def dispatch(script, args, declined=False):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name in ("sudo.sh", "sudo-linux.sh", "confirm-passkey.sh"):
            target = root / name
            target.write_text((SCRIPTS / name).read_text())
            target.chmod(0o700)
        (root / "approve.sh").write_text("request_approval() { echo approval-grant=${GRANT_SECONDS:-300}; return ${DECLINED:-0}; }\n")
        for name in ("native_click_linux", "press_passkey_linux"):
            (root / f"{name}.py").write_text("import sys\nprint('helper ' + ' '.join(sys.argv[1:]))\n")
        for name, text in (("uname", "echo Linux"), ("xdotool", "exit 77")):
            target = root / name
            target.write_text("#!/bin/sh\n" + text + "\n")
            target.chmod(0o700)
        env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"], DECLINED=str(int(declined)))
        return subprocess.run(["bash", str(root / script), *args], env=env, capture_output=True, text=True)


def test_passkey_dispatch_keeps_fresh_approval():
    result = dispatch("confirm-passkey.sh", ["example.com"])
    assert result.returncode == 0, result.stderr
    assert "approval-grant=0" in result.stdout
    assert "helper example.com" in result.stdout


def test_declined_passkey_never_runs_helper():
    result = dispatch("confirm-passkey.sh", ["example.com"], declined=True)
    assert result.returncode == 1
    assert "helper" not in result.stdout


def test_native_click_dispatches_after_approval():
    result = dispatch("sudo.sh", ["https://accounts.example.com", "--title", "Sign in", "--via", "google", "--window-id", "42", "--click", "100,200"])
    assert result.returncode == 0, result.stderr
    assert "helper 42 Sign in 100,200" in result.stdout


def test_declined_native_click_never_runs_helper():
    result = dispatch("sudo.sh", ["https://accounts.example.com", "--title", "Sign in", "--via", "google", "--window-id", "42", "--click", "100,200"], declined=True)
    assert result.returncode == 1
    assert "helper" not in result.stdout


def test_native_click_requires_complete_explicit_arguments():
    for extra in (["--click", "100,200"], ["--window-id", "42"], ["--window-id", "42", "--click", "100,200"]):
        result = dispatch("sudo.sh", ["https://accounts.example.com", *extra])
        assert result.returncode == 3
        assert "approval" not in result.stdout


def test_existing_google_approval_remains_no_click():
    result = dispatch("sudo.sh", ["https://accounts.example.com", "--title", "Sign in", "--via", "google"])
    assert result.returncode == 0, result.stderr
    assert "approved: google" in result.stdout
    assert "helper" not in result.stdout


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.FunctionTestCase(value) for name, value in sorted(globals().items()) if name.startswith("test_"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
