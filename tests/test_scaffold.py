from pathlib import Path

from conftest import run_script


def test_scaffold_creates_tree_and_seeds(tmp_path: Path) -> None:
    root = tmp_path / "fresh"
    r = run_script("scaffold_docs.py", str(root), "--project", "Demo")
    assert r.returncode == 0
    assert (root / "docs" / "specs").is_dir()
    assert (root / "docs" / "decisions" / "ADR-template.md").is_file() is False  # templates live in docs/templates
    assert (root / "docs" / "templates" / "ADR-template.md").is_file()
    assert (root / "docs" / "README.md").read_text(encoding="utf-8").startswith("# Demo")
    assert (root / "docs" / "changes" / "CHANGELOG.md").is_file()


def test_scaffold_is_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    run_script("scaffold_docs.py", str(root))
    r2 = run_script("scaffold_docs.py", str(root))
    assert r2.returncode == 0
    assert "0 created" in r2.stdout
    assert "0 failed" in r2.stdout


def test_scaffold_never_overwrites_content(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    run_script("scaffold_docs.py", str(root))
    readme = root / "docs" / "README.md"
    readme.write_text("# Custom index\n", encoding="utf-8")
    r = run_script("scaffold_docs.py", str(root))
    assert r.returncode == 0
    assert readme.read_text(encoding="utf-8") == "# Custom index\n"


def test_scaffold_dry_run_touches_nothing(tmp_path: Path) -> None:
    root = tmp_path / "dry"
    r = run_script("scaffold_docs.py", str(root), "--dry-run")
    assert r.returncode == 0
    assert "created" in r.stdout
    assert not root.exists()
