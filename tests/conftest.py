"""Shared fixtures: run scripts as black boxes against tmp_path fixtures."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"


def run_script(name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )


@pytest.fixture
def scaffolded(tmp_path: Path) -> Path:
    """A fresh scaffolded repo root."""
    root = tmp_path / "repo"
    r = run_script("scaffold_docs.py", str(root), "--project", "Fixture")
    assert r.returncode == 0, r.stderr + r.stdout
    return root


def git_fixture(root: Path, *commits: tuple[list[str], str]) -> None:
    """Init a git repo at root; each commit is (files-with-content, message)."""
    def g(*args: str) -> None:
        r = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr

    g("init", "-q")
    g("config", "user.email", "fixture@test")
    g("config", "user.name", "Fixture")
    for files, message in commits:
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8", newline="\n")
        # stage only this commit's files — `add -A` would sweep the pre-seeded
        # scaffold (incl. the changelog) into the first commit and skew coverage
        g("add", "--", *files.keys())
        g("commit", "-q", "-m", message)
