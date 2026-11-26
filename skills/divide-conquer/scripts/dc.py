#!/usr/bin/env python3
"""divide-conquer bookkeeping: assignment folders, leak checks, verification, integration."""
import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"
WORKER_GUIDE = SKILL.parent / "silo-worker" / "SKILL.md"
REQUIRED_HEADINGS = [
    "## Problem",
    "## Environment",
    "## Public interface",
    "## Rules",
    "## Errors",
    "## Worked examples",
    "## Deliverables",
]
MIN_EXAMPLES = 5
MIN_TERMS = 5
FROZEN = ["ASSIGNMENT.md", "run_tests.sh", "tests/acceptance", "starter"]


def die(msg):
    sys.exit(f"ERROR: {msg}")


def dc_dir(project):
    d = Path(project).resolve() / ".dc"
    if not d.is_dir():
        die(f"{d} not found. Run: dc.py init {project}")
    return d


def load(project):
    return json.loads((dc_dir(project) / "state.json").read_text())


def save(project, state):
    (dc_dir(project) / "state.json").write_text(json.dumps(state, indent=2) + "\n")


def folder(state, aid):
    if aid not in state["assignments"]:
        die(f"unknown assignment {aid}. Known: {', '.join(state['assignments']) or 'none'}")
    return Path(state["batch_dir"]) / aid


def text_files(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "HOW_TO_WORK.md":
            try:
                yield p, p.read_text()
            except UnicodeDecodeError:
                continue


def fingerprint(root):
    h = hashlib.sha256()
    for rel in FROZEN:
        p = root / rel
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else []
        for f in files:
            if "__pycache__" in f.parts:
                continue
            h.update(str(f.relative_to(root)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def secret_terms(project):
    lines = (dc_dir(project) / "secret_terms.txt").read_text().splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def cmd_init(a):
    project = Path(a.project).resolve()
    d = project / ".dc"
    if d.exists():
        die(f"{d} already exists")
    d.mkdir(parents=True)
    home = Path(os.environ.get("DC_HOME", Path.home() / ".dc-assignments"))
    batch = home / f"batch-{secrets.token_hex(3)}"
    batch.mkdir(parents=True)
    shutil.copy(ASSETS / "PLAN.md", d / "PLAN.md")
    shutil.copy(ASSETS / "secret_terms.txt", d / "secret_terms.txt")
    (d / "state.json").write_text(json.dumps({"batch_dir": str(batch), "assignments": {}}, indent=2) + "\n")
    exclude = project / ".git" / "info" / "exclude"
    if exclude.parent.is_dir():
        with exclude.open("a") as f:
            f.write("\n.dc/\n")
    print(f"private notes (never show to a worker): {d}")
    print(f"assignment folders go in:               {batch}")
    print(f"next: fill in {d / 'secret_terms.txt'} and {d / 'PLAN.md'}")


def cmd_new(a):
    state = load(a.project)
    if not re.fullmatch(r"A\d\d", a.id):
        die("assignment id must look like A01, A02, ...")
    if a.id in state["assignments"]:
        die(f"{a.id} already exists")
    if not WORKER_GUIDE.is_file():
        die(f"worker guide missing: {WORKER_GUIDE} (install the silo-worker skill next to divide-conquer)")
    root = Path(state["batch_dir"]) / a.id
    for sub in ("src", "tests/acceptance", "starter"):
        (root / sub).mkdir(parents=True)
    shutil.copy(ASSETS / "ASSIGNMENT.md", root / "ASSIGNMENT.md")
    shutil.copy(ASSETS / "run_tests.sh", root / "run_tests.sh")
    (root / "run_tests.sh").chmod(0o755)
    guide = WORKER_GUIDE.read_text()
    guide = re.sub(r"\A---\n.*?\n---\n", "", guide, flags=re.S)
    (root / "HOW_TO_WORK.md").write_text(guide.lstrip())
    state["assignments"][a.id] = {"dest": a.dest, "tests_dest": a.tests_dest, "status": "draft"}
    save(a.project, state)
    print(f"created {root}")
    print(f"next: fill in {root / 'ASSIGNMENT.md'}, then: dc.py check {a.project} {a.id}")


def check_one(project, state, aid, terms):
    root = folder(state, aid)
    problems = []
    for path, text in text_files(root):
        rel = path.relative_to(root)
        for term in terms:
            if term.lower() in str(rel).lower():
                problems.append(f"LEAK  {rel}: file name contains secret term '{term}'")
            for n, line in enumerate(text.splitlines(), 1):
                if term.lower() in line.lower():
                    problems.append(f"LEAK  {rel}:{n}: contains secret term '{term}'")
    brief = (root / "ASSIGNMENT.md").read_text()
    for n, line in enumerate(brief.splitlines(), 1):
        if "<<" in line:
            problems.append(f"EMPTY ASSIGNMENT.md:{n}: placeholder not filled in: {line.strip()[:60]}")
    for h in REQUIRED_HEADINGS:
        if h not in brief:
            problems.append(f"MISSING ASSIGNMENT.md: section '{h}'")
    examples = len(re.findall(r"^### Example", brief, flags=re.M))
    if examples < MIN_EXAMPLES:
        problems.append(f"THIN  ASSIGNMENT.md: {examples} worked examples, need at least {MIN_EXAMPLES} ('### Example N' headings)")
    if not os.access(root / "run_tests.sh", os.X_OK):
        problems.append("MISSING run_tests.sh is absent or not executable")
    return problems


def cmd_check(a):
    state = load(a.project)
    terms = secret_terms(a.project)
    if len(terms) < MIN_TERMS:
        die(f".dc/secret_terms.txt lists {len(terms)} terms; list at least {MIN_TERMS} before checking")
    ids = [a.id] if a.id else list(state["assignments"])
    bad = False
    for aid in ids:
        problems = check_one(a.project, state, aid, terms)
        if problems:
            bad = True
            print(f"{aid}: FAIL")
            for p in problems:
                print(f"  {p}")
        else:
            print(f"{aid}: OK")
            if state["assignments"][aid]["status"] == "draft":
                state["assignments"][aid]["status"] = "checked"
    save(a.project, state)
    if bad:
        sys.exit(1)


def cmd_prompt(a):
    state = load(a.project)
    entry = state["assignments"].get(a.id) or die(f"unknown assignment {a.id}")
    root = folder(state, a.id)
    if check_one(a.project, state, a.id, secret_terms(a.project)):
        die(f"{a.id} does not pass the check. Run: dc.py check {a.project} {a.id}")
    entry["fingerprint"] = fingerprint(root)
    entry["status"] = "dispatched"
    save(a.project, state)
    revision = " This is a revision round: read FEEDBACK.md first." if (root / "FEEDBACK.md").exists() else ""
    print(
        f"You have one self-contained programming assignment in the folder {root}\n"
        f"1. Read {root}/HOW_TO_WORK.md and follow it exactly.\n"
        f"2. Read {root}/ASSIGNMENT.md and complete it.{revision}\n"
        f"Work only inside that folder: do not read, search or list anything outside it.\n"
        f"When finished, reply with only the Status line from SUBMISSION.md."
    )


def cmd_verify(a):
    state = load(a.project)
    root = folder(state, a.id)
    entry = state["assignments"][a.id]
    sub = root / "SUBMISSION.md"
    if not sub.is_file():
        die(f"{a.id}: no SUBMISSION.md. The worker did not finish; dispatch it again.")
    m = re.search(r"^Status:\s*(\w+)", sub.read_text(), flags=re.M)
    status = m.group(1).upper() if m else "MISSING"
    if status != "DONE":
        print(f"{a.id}: worker status is {status}, not DONE. Read {sub}, answer in FEEDBACK.md, dispatch again.")
        entry["status"] = "needs-answer"
        save(a.project, state)
        sys.exit(1)
    if entry.get("fingerprint") != fingerprint(root):
        die(f"{a.id}: the worker changed ASSIGNMENT.md, run_tests.sh, tests/acceptance or starter. Reject the submission.")
    if not any(p.is_file() for p in (root / "src").rglob("*")):
        die(f"{a.id}: src/ is empty")
    try:
        run = subprocess.run(["./run_tests.sh"], cwd=root, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        die(f"{a.id}: run_tests.sh did not finish within 15 minutes")
    tail = "\n".join((run.stdout + run.stderr).splitlines()[-15:])
    print(tail)
    if run.returncode != 0:
        entry["status"] = "tests-failed"
        save(a.project, state)
        print(f"\n{a.id}: TESTS FAILED. Paste the output above into {root}/FEEDBACK.md and dispatch again.")
        sys.exit(1)
    entry["status"] = "verified"
    save(a.project, state)
    print(f"\n{a.id}: VERIFIED. next: dc.py integrate {a.project} {a.id}")


def cmd_integrate(a):
    state = load(a.project)
    root = folder(state, a.id)
    entry = state["assignments"][a.id]
    if entry["status"] not in ("verified", "integrated"):
        die(f"{a.id} is '{entry['status']}', not verified. Run: dc.py verify {a.project} {a.id}")
    project = Path(a.project).resolve()
    pairs = [(root / "src", project / entry["dest"])]
    if entry.get("tests_dest"):
        pairs.append((root / "tests", project / entry["tests_dest"]))
    for src, dest in pairs:
        dest.mkdir(parents=True, exist_ok=True)
        for f in sorted(p for p in src.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            target = dest / f.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            print(f"copied {target.relative_to(project)}")
    entry["status"] = "integrated"
    save(a.project, state)


def cmd_status(a):
    state = load(a.project)
    print(f"assignments folder: {state['batch_dir']}")
    for aid, e in state["assignments"].items():
        print(f"{aid}  {e['status']:<13} -> {e['dest']}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn, extra in [
        ("init", cmd_init, []),
        ("new", cmd_new, ["id"]),
        ("check", cmd_check, ["id?"]),
        ("prompt", cmd_prompt, ["id"]),
        ("verify", cmd_verify, ["id"]),
        ("integrate", cmd_integrate, ["id"]),
        ("status", cmd_status, []),
    ]:
        s = sub.add_parser(name)
        s.add_argument("project")
        for arg in extra:
            s.add_argument("id", nargs="?") if arg.endswith("?") else s.add_argument("id")
        if name == "new":
            s.add_argument("--dest", required=True, help="folder inside the project that receives src/")
            s.add_argument("--tests-dest", help="folder inside the project that receives tests/")
        s.set_defaults(fn=fn)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
