import json
from pathlib import Path

from conftest import run_script


def test_scaffolded_tree_is_strict_clean(scaffolded: Path) -> None:
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert r.returncode == 0, r.stdout
    assert "0 errors, 0 warnings" in r.stdout


def test_rfc_uppercase_outside_allowlist_fails(scaffolded: Path) -> None:
    (scaffolded / "docs" / "notes.md").write_text(
        "# Notes\n\nYou MUST update the changelog.\n", encoding="utf-8"
    )
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert r.returncode == 1
    assert "uppercase MUST outside allowlisted page" in r.stdout


def test_rfc_uppercase_inside_allowlist_passes(scaffolded: Path) -> None:
    (scaffolded / "docs" / "decisions" / "ADR-0001-x.md").write_text(
        "# ADR-0001: x\n\nReleases MUST update the changelog.\n", encoding="utf-8"
    )
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert r.returncode == 0, r.stdout


def test_sentence_cap_warns_but_does_not_fail(scaffolded: Path) -> None:
    long = " ".join(["word"] * 25) + "."
    (scaffolded / "AGENTS.md").write_text(f"# Agents\n\n{long}\n", encoding="utf-8")
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert r.returncode == 0  # warnings do not trip --strict
    assert "sentence has" in r.stdout


def test_banned_synonym_via_config(scaffolded: Path) -> None:
    (scaffolded / "docs-ops.json").write_text(
        json.dumps({"banned_synonyms": {"flow": "pipeline"}}), encoding="utf-8"
    )
    (scaffolded / "docs" / "notes.md").write_text("# Flow\n\nThe flow works.\n", encoding="utf-8")
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert r.returncode == 1
    assert "use 'pipeline'" in r.stdout


def test_bom_config_is_tolerated(scaffolded: Path) -> None:
    # Windows editors write a UTF-8 BOM; the checker must still parse config.
    # Templates quote everyday words ("data flow"), so synonym bans exempt them.
    (scaffolded / "docs-ops.json").write_bytes(
        b"\xef\xbb\xbf"
        + json.dumps(
            {
                "banned_synonyms": {"flow": "pipeline"},
                "synonym_exempt": ["docs/templates/**"],
            }
        ).encode()
    )
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert r.returncode == 0, r.stdout


def test_code_blocks_are_ignored(scaffolded: Path) -> None:
    (scaffolded / "docs" / "notes.md").write_text(
        "# N\n\n```python\nx = 'You MUST not count this very long sentence inside a fence at all'\n```\n",
        encoding="utf-8",
    )
    r = run_script("check_docs.py", "--strict", "--root", str(scaffolded))
    assert "uppercase MUST" not in r.stdout
    assert "sentence has" not in r.stdout
