#!/usr/bin/env python3
"""Scaffold or repair an SDLC-aligned docs/ tree. Stdlib only.

Usage:
    python scaffold_docs.py <repo-root> [--project NAME] [--dry-run] [--repair]

Creates the docs/ directory skeleton and seeds missing files from this skill's
templates/. Never overwrites a file that already has content (even with
--repair, which only fills zero-byte placeholders). Exit 0 on success,
1 on any failed write.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

DIRS = [
    "docs",
    "docs/specs",
    "docs/plans",
    "docs/standards",
    "docs/decisions",
    "docs/architecture",
    "docs/architecture/diagrams",
    "docs/qa",
    "docs/qa/runs",
    "docs/qa/evidence",
    "docs/reviews",
    "docs/research",
    "docs/changes",
    "docs/revisions",
    "docs/templates",
]

# (target path under repo root, template filename or None, substitute project name)
SEEDS = [
    ("docs/README.md", "docs-README.md", True),
    ("docs/CONTRIBUTING.md", "CONTRIBUTING.md", False),
    ("docs/standards/writing-guide.md", "writing-guide-seed.md", False),
    ("docs/changes/CHANGELOG.md", "CHANGELOG.md", False),
    ("docs/templates/ADR-template.md", "ADR-template.md", False),
    ("docs/templates/spec-issue-template.md", "spec-issue-template.md", False),
    ("docs/templates/plan-template.md", "plan-template.md", False),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo_root", type=Path)
    ap.add_argument("--project", default="Project", help="name used in the README seed")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repair", action="store_true", help="fill zero-byte placeholder files")
    args = ap.parse_args()

    root: Path = args.repo_root.resolve()
    # bootstrap case: a brand-new repo root may not exist yet — create it
    if not root.exists() and not args.dry_run:
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"error: cannot create {root}: {exc}", file=sys.stderr)
            return 1
    if not args.dry_run and not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    created: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for rel in DIRS:
        d = root / rel
        if d.is_dir():
            skipped.append(rel + "/")
            continue
        if args.dry_run:
            created.append(rel + "/")
            continue
        try:
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel + "/")
        except OSError as exc:
            failed.append(f"{rel}/: {exc}")

    for rel, tmpl, substitute in SEEDS:
        target = root / rel
        if target.is_file() and target.stat().st_size > 0:
            skipped.append(rel)
            continue
        if target.is_file() and target.stat().st_size == 0 and not args.repair:
            skipped.append(rel + " (empty; --repair to fill)")
            continue
        src = TEMPLATES / tmpl
        if not src.is_file():
            failed.append(f"{rel}: template missing {src}")
            continue
        if args.dry_run:
            created.append(rel)
            continue
        try:
            text = src.read_text(encoding="utf-8")
            if substitute:
                text = text.replace("<Project>", args.project)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
            created.append(rel)
        except OSError as exc:
            failed.append(f"{rel}: {exc}")

    for item in created:
        print(f"created  {item}")
    for item in skipped:
        print(f"skipped  {item}")
    for item in failed:
        print(f"FAILED   {item}", file=sys.stderr)
    print(f"\n{len(created)} created, {len(skipped)} skipped, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
