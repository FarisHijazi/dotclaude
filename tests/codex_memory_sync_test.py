"""Exercise the real one-way mirror only in temporary home directories."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "sync-codex-memory.py"


def layout(home):
    source = home / ".claude" / "memory"
    target = home / ".codex" / "memory"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "MEMORY.md").write_text("# Memory\n")
    return source, target


def run(home, *arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--home", str(home), *arguments],
        capture_output=True, text=True, timeout=15,
    )


def contents(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_mirrors_add_update_and_delete_without_source_changes(tmp_path):
    source, target = layout(tmp_path)
    (source / "nested").mkdir()
    (source / "nested" / "note.md").write_text("first")
    original = contents(source)
    assert run(tmp_path).returncode == 0
    assert contents(target) == original
    (source / "nested" / "note.md").write_text("second")
    (source / "new.md").write_text("new")
    (target / "target-only.md").write_text("discard")
    original = contents(source)
    assert run(tmp_path).returncode == 0
    assert contents(target) == original == contents(source)
    (source / "nested" / "note.md").unlink()
    (source / "nested").rmdir()
    assert run(tmp_path).returncode == 0
    assert not (target / "nested").exists()
    assert contents(target) == contents(source)


def test_corrects_same_size_same_time_target_edit_and_noop_does_not_write(tmp_path):
    source, target = layout(tmp_path)
    (source / "note.md").write_text("source")
    assert run(tmp_path).returncode == 0
    (target / "note.md").write_text("target")
    source_stat = (source / "note.md").stat()
    os.utime(target / "note.md", ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
    assert run(tmp_path).returncode == 0
    assert (target / "note.md").read_text() == "source"
    assert (source / "note.md").read_text() == "source"
    before = {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in target.rglob("*")}
    result = run(tmp_path)
    assert result.returncode == 0
    assert not result.stdout.strip()
    assert {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in target.rglob("*")} == before


def test_dry_run_lists_exact_deletion_and_does_not_write(tmp_path):
    source, target = layout(tmp_path)
    (target / "old.md").write_text("keep until apply")
    source_before, target_before = contents(source), contents(target)
    result = run(tmp_path, "--dry-run")
    assert result.returncode == 0
    assert "old.md" in result.stdout and "deleting" in result.stdout
    assert contents(source) == source_before
    assert contents(target) == target_before
    assert not (tmp_path / ".claude" / ".memory-sync.lock").exists()


@pytest.mark.parametrize("remove_index", [True, False])
def test_missing_or_empty_index_cannot_erase_mirror(tmp_path, remove_index):
    source, target = layout(tmp_path)
    (target / "keep.md").write_text("keep")
    if remove_index:
        (source / "MEMORY.md").unlink()
    else:
        (source / "MEMORY.md").write_text("")
    result = run(tmp_path)
    assert result.returncode != 0
    assert (target / "keep.md").read_text() == "keep"


@pytest.mark.parametrize("root", [".claude", ".codex"])
@pytest.mark.parametrize("nested", [True, False])
def test_refuses_symlink_roots_or_children(tmp_path, root, nested):
    source, target = layout(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.md").write_text("untouched")
    if nested:
        (tmp_path / root / "memory" / "link").symlink_to(outside, target_is_directory=True)
    else:
        (tmp_path / root).rename(tmp_path / "saved")
        (tmp_path / root).symlink_to(tmp_path / "saved", target_is_directory=True)
    result = run(tmp_path)
    assert result.returncode != 0
    assert "symlink" in result.stderr
    assert (outside / "keep.md").read_text() == "untouched"


def test_refuses_target_alias_of_source(tmp_path):
    source, target = layout(tmp_path)
    target.rmdir()
    target.symlink_to(source, target_is_directory=True)
    result = run(tmp_path)
    assert result.returncode != 0
    assert contents(source) == {"MEMORY.md": b"# Memory\n"}


def test_refuses_hardlinked_files(tmp_path):
    source, target = layout(tmp_path)
    os.link(source / "MEMORY.md", target / "MEMORY.md")
    result = run(tmp_path)
    assert result.returncode != 0
    assert "hard-linked" in result.stderr


def test_fixed_direction_rejects_source_destination_arguments(tmp_path):
    source, target = layout(tmp_path)
    result = run(tmp_path, "--source", str(target), "--destination", str(source))
    assert result.returncode != 0
    assert contents(source) == {"MEMORY.md": b"# Memory\n"}
    assert contents(target) == {}
