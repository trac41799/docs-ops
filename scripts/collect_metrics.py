#!/usr/bin/env python3
"""Collect a scored docs-health report for an adopting repo.

Stdlib + git CLI only. The target repo's content is never modified; the only
write is the run report JSON (default <root>/metrics/runs/).

Usage:
    python collect_metrics.py --root <repo> [--budgets <json>] [--out <dir>]
                              [--window-days N] [--no-git]

Sections:
    structure  scaffold-area presence (same tree scaffold_docs.py creates)
    prose      check_docs.py scores — reused as the single prose-rule source
    links      broken relative markdown links
    process    git-derived: changelog coverage of behavior commits,
               ADR/plan/spec counts, Delivered-vs-Deferred presence
    staleness  days since last commit per docs area
    budgets    pass/fail against budgets.json

Exit codes: 0 all budgets pass · 1 budget failure · 2 operational error.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
COUNTS_RE = re.compile(r"(\d+) errors, (\d+) warnings")

# same pruning as check_docs.py — a monorepo walk without this exceeds 120s
EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".next",
    "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".eggs", "site-packages",
}

DEFAULT_BUDGETS = {
    "max_prose_errors": 0,
    "max_broken_links": 0,
    "min_changelog_coverage_pct": 80.0,
    "max_structure_missing": 0,
    "code_globs": ["backend/**", "frontend/**", "src/**", "app/**", "lib/**", "api/**"],
    "changelog_paths": [
        "docs/changes/CHANGELOG.md",
        "changes/CHANGELOG.md",
        "CHANGELOG.md",
    ],
    "window_days": 30,
}

AREAS = [
    "docs/specs",
    "docs/plans",
    "docs/standards",
    "docs/decisions",
    "docs/architecture",
    "docs/qa",
]


def git(root: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip() or 'failed'}")
    return r.stdout


def has_commits(root: Path) -> bool:
    r = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def collect_structure(root: Path) -> dict:
    present = [a for a in AREAS if (root / a).is_dir()]
    missing = [a for a in AREAS if not (root / a).is_dir()]
    return {"present": len(present), "total": len(AREAS), "missing": missing}


def collect_prose(root: Path) -> dict:
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_docs.py"), "--strict", "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = ANSI_RE.sub("", r.stdout or "")
    m = COUNTS_RE.search(out)
    if not m:
        return {"errors": None, "warnings": None, "parse_error": out[-200:]}
    return {"errors": int(m.group(1)), "warnings": int(m.group(2))}


def collect_links(root: Path) -> dict:
    checked = 0
    broken: list[str] = []
    md_files_list: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")
        ]
        md_files_list.extend(Path(dirpath) / fn for fn in filenames if fn.endswith(".md"))
    for f in md_files_list:
        text = f.read_text(encoding="utf-8-sig", errors="replace")
        for m in MD_LINK_RE.finditer(text):
            target = m.group(1).strip().strip("<>").split()[0] if m.group(1).strip() else ""
            if not target or target.startswith(("http://", "https://", "mailto:", "#", "ftp:")):
                continue
            if target.startswith("/"):  # site-root absolute — not resolvable here
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            checked += 1
            resolved = (f.parent / path_part).resolve()
            if not resolved.exists():
                rel = f.relative_to(root).as_posix()
                broken.append(f"{rel} -> {target}")
    return {"checked": checked, "broken": broken}


def _commit_files(log: str) -> list[tuple[str, list[str]]]:
    """Parse `git log --name-only --pretty=format:%H%x01%s` into (subject, files)."""
    commits: list[tuple[str, list[str]]] = []
    subject = ""
    files: list[str] = []
    for line in log.splitlines():
        if "\x01" in line:
            if subject or files:
                commits.append((subject, files))
            subject = line.split("\x01", 1)[1]
            files = []
        elif line.strip():
            files.append(line.strip())
    if subject or files:
        commits.append((subject, files))
    return commits


def _matches_any(files: list[str], globs: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(f, g) for f in files for g in globs)


def collect_process(root: Path, budgets: dict, window_days: int) -> dict:
    if not has_commits(root):
        return {"git": False}
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    log = git(
        root,
        "log",
        f"--since={since}",
        "--no-merges",
        "--name-only",
        "--pretty=format:%H%x01%s",
    )
    commits = _commit_files(log)
    code_globs = list(budgets["code_globs"])
    changelog_paths = set(budgets["changelog_paths"])
    eligible = [c for c in commits if _matches_any(c[1], code_globs)]
    covered = [c for c in eligible if any(f in changelog_paths for f in c[1])]
    coverage = (len(covered) / len(eligible) * 100.0) if eligible else None

    adrs = sorted((root / "docs" / "decisions").glob("ADR-*.md")) if (
        root / "docs" / "decisions"
    ).is_dir() else []
    specs_dir = root / "docs" / "specs"
    specs = sorted(specs_dir.glob("*.md")) if specs_dir.is_dir() else []
    plans_dir = root / "docs" / "plans"
    plans = sorted(plans_dir.glob("*.md")) if plans_dir.is_dir() else []
    deferred_ok = sum(1 for s in specs if re.search(r"\bDeferred\b", s.read_text(encoding="utf-8-sig", errors="replace")))
    new_adr_log = git(root, "log", f"--since={since}", "--name-only", "--pretty=format:%H", "--", "docs/decisions")
    new_adrs = len({l for l in new_adr_log.splitlines() if l.startswith("ADR-") or l.endswith(".md") and "decisions" in l})

    return {
        "git": True,
        "window_days": window_days,
        "behavior_commits": len(eligible),
        "changelog_covered": len(covered),
        "changelog_coverage_pct": round(coverage, 1) if coverage is not None else None,
        "uncovered_subjects": [c[0] for c in eligible if c not in covered][:10],
        "adr_count": len(adrs),
        "new_adrs_in_window": new_adrs,
        "spec_count": len(specs),
        "plan_count": len(plans),
        "specs_with_deferred": deferred_ok,
        "specs_total": len(specs),
    }


def collect_staleness(root: Path) -> dict:
    if not has_commits(root):
        return {"git": False}
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    out: dict[str, float | None] = {}
    for a in AREAS:
        if not (root / a).is_dir():
            out[a] = None
            continue
        r = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%ct", "--", a],
            capture_output=True,
            text=True,
        )
        ts = r.stdout.strip()
        out[a] = round((now - int(ts)) / 86400.0, 1) if ts else None
    return {"git": True, "days_since_touch": out}


def evaluate_budgets(budgets: dict, structure: dict, prose: dict, links: dict, process: dict) -> dict:
    failures: list[str] = []
    if structure["missing"]:
        n = len(structure["missing"])
        if n > budgets["max_structure_missing"]:
            failures.append(f"structure: {n} missing areas (budget {budgets['max_structure_missing']})")
    if prose.get("errors") is not None and prose["errors"] > budgets["max_prose_errors"]:
        failures.append(f"prose: {prose['errors']} errors (budget {budgets['max_prose_errors']})")
    if len(links["broken"]) > budgets["max_broken_links"]:
        failures.append(f"links: {len(links['broken'])} broken (budget {budgets['max_broken_links']})")
    cov = process.get("changelog_coverage_pct")
    if cov is not None and cov < budgets["min_changelog_coverage_pct"]:
        failures.append(
            f"changelog coverage {cov}% < budget {budgets['min_changelog_coverage_pct']}%"
        )
    return {"pass": not failures, "failures": failures}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--budgets", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--window-days", type=int, default=None)
    ap.add_argument("--no-git", action="store_true")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    budgets = dict(DEFAULT_BUDGETS)
    bfile = args.budgets or (SCRIPTS.parent / "metrics" / "budgets.json")
    if bfile.is_file():
        try:
            budgets.update(json.loads(bfile.read_text(encoding="utf-8-sig")))
        except json.JSONDecodeError as exc:
            print(f"error: {bfile}: {exc}", file=sys.stderr)
            return 2

    window = args.window_days or int(budgets["window_days"])
    structure = collect_structure(root)
    prose = collect_prose(root)
    links = collect_links(root)
    process = {"git": False} if args.no_git else collect_process(root, budgets, window)
    staleness = {"git": False} if args.no_git else collect_staleness(root)
    verdict = evaluate_budgets(budgets, structure, prose, links, process)

    sha = ""
    if process.get("git"):
        try:
            sha = git(root, "rev-parse", "--short", "HEAD").strip()
        except RuntimeError:
            sha = ""
    report = {
        "meta": {
            "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "repo": str(root),
            "commit": sha,
            "tool": "docs-ops collect_metrics",
        },
        "structure": structure,
        "prose": prose,
        "links": links,
        "process": process,
        "staleness": staleness,
        "budgets": {k: budgets[k] for k in (
            "max_prose_errors", "max_broken_links",
            "min_changelog_coverage_pct", "max_structure_missing",
        )},
        "verdict": verdict,
    }

    out_dir = args.out or (root / "metrics" / "runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    out_file = out_dir / f"docs-health-{day}-{sha or 'nogit'}.json"
    out_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

    # stdout summary — the numbers a human reads first
    print(f"docs-health {report['meta']['date']} @ {sha or 'nogit'}")
    print(f"  structure : {structure['present']}/{structure['total']} areas"
          + (f" missing={structure['missing']}" if structure['missing'] else ""))
    print(f"  prose     : {prose.get('errors')} errors, {prose.get('warnings')} warnings")
    print(f"  links     : {links['checked']} checked, {len(links['broken'])} broken")
    if process.get("git"):
        cov = process["changelog_coverage_pct"]
        print(f"  process   : changelog coverage {cov if cov is not None else 'n/a'}% "
              f"({process['changelog_covered']}/{process['behavior_commits']} behavior commits, "
              f"{window}d window); ADRs {process['adr_count']} (+{process['new_adrs_in_window']}); "
              f"specs {process['spec_count']} deferred-table {process['specs_with_deferred']}/{process['specs_total']}; "
              f"plans {process['plan_count']}")
    else:
        print("  process   : skipped (no git or --no-git)")
    print(f"  verdict   : {'PASS' if verdict['pass'] else 'FAIL — ' + '; '.join(verdict['failures'])}")
    print(f"  report    : {out_file}")
    return 0 if verdict["pass"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
