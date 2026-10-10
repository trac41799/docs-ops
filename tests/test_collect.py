import json
from pathlib import Path

from conftest import git_fixture, run_script


def collect(root: Path, *extra: str) -> tuple[int, str]:
    r = run_script("collect_metrics.py", "--root", str(root), *extra)
    return r.returncode, r.stdout


def test_collect_on_scaffolded_fixture_passes(scaffolded: Path, tmp_path: Path) -> None:
    code, out = collect(scaffolded, "--out", str(tmp_path / "runs"), "--no-git")
    assert code == 0, out
    assert "PASS" in out
    runs = list((tmp_path / "runs").glob("docs-health-*.json"))
    assert len(runs) == 1
    report = json.loads(runs[0].read_text(encoding="utf-8"))
    assert report["structure"]["missing"] == []
    assert report["prose"]["errors"] == 0
    assert report["verdict"]["pass"] is True


def test_changelog_coverage_math(scaffolded: Path, tmp_path: Path) -> None:
    git_fixture(
        scaffolded,
        ({"src/app.py": "x = 1\n"}, "feat: behavior without changelog"),
        (
            {"src/other.py": "y = 2\n", "docs/changes/CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n\n### Added\n- thing\n"},
            "feat: behavior with changelog",
        ),
    )
    code, out = collect(scaffolded, "--out", str(tmp_path / "runs"), "--window-days", "36500")
    runs = sorted((tmp_path / "runs").glob("docs-health-*.json"))
    report = json.loads(runs[-1].read_text(encoding="utf-8"))
    assert report["process"]["behavior_commits"] == 2
    assert report["process"]["changelog_covered"] == 1
    assert report["process"]["changelog_coverage_pct"] == 50.0
    # default budget is 80% — 50% must FAIL the verdict
    assert code == 1
    assert report["verdict"]["pass"] is False
    assert any("changelog coverage" in f for f in report["verdict"]["failures"])


def test_broken_link_detected(scaffolded: Path, tmp_path: Path) -> None:
    (scaffolded / "docs" / "notes.md").write_text(
        "# N\n\nSee [missing](specs/nope.md).\n", encoding="utf-8"
    )
    code, out = collect(scaffolded, "--out", str(tmp_path / "runs"), "--no-git")
    assert code == 1
    assert "broken" in out


def test_budget_override_raises_coverage_bar(scaffolded: Path, tmp_path: Path) -> None:
    git_fixture(
        scaffolded,
        ({"src/a.py": "1\n", "docs/changes/CHANGELOG.md": "# C\n"}, "feat: covered"),
    )
    b = tmp_path / "budgets.json"
    b.write_text(json.dumps({"min_changelog_coverage_pct": 100.0}), encoding="utf-8")
    code, out = collect(scaffolded, "--budgets", str(b), "--out", str(tmp_path / "runs"), "--window-days", "36500")
    assert code == 0, out
