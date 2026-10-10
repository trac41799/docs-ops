#!/usr/bin/env python3
"""Copy this skill folder into every harness skills directory on this machine.

Usage:
    python propagate.py [--list] [--target NAME] [--dry-run]

The canonical copy is this folder (normally ~/.agents/skills/docs-ops). Each
target receives a full plain copy — every harness surveyed on this machine
consumes the same Agent-Skills folder format (SKILL.md + YAML frontmatter).
Existing target dirs are replaced so re-propagation stays idempotent.

Not targeted: ~/.config/opencode/skills — OpenCode natively scans
~/.agents/skills, and a second copy would double-list the skill. Cursor's
system pack (~/.cursor/skills-cursor) is vendor-owned and left alone.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# harness skills roots, relative to the user home
TARGETS = [
    ".claude/skills",
    ".codex/skills",
    ".cursor/skills",
    ".copilot/skills",
    ".gemini/skills",
    ".qwen/skills",
    ".roo/skills",
    ".iflow/skills",
    ".factory/skills",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="list targets and exit")
    ap.add_argument("--target", help="propagate to a single target dir name")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(__file__).resolve().parent.parent
    if not (src / "SKILL.md").is_file():
        print(f"error: {src} has no SKILL.md — run from inside the skill folder", file=sys.stderr)
        return 1

    home = Path.home()
    targets = TARGETS
    if args.target:
        targets = [t for t in TARGETS if Path(t).name == args.target]
        if not targets:
            print(f"error: unknown target {args.target!r}; known: {[Path(t).name for t in TARGETS]}", file=sys.stderr)
            return 1

    if args.list:
        for t in TARGETS:
            d = home / t / src.name
            state = "present" if d.is_dir() else "absent"
            print(f"{t}/{src.name}: {state}")
        return 0

    failed = 0
    for rel in targets:
        dest_dir = home / rel
        dest = dest_dir / src.name
        if not dest_dir.is_dir():
            print(f"SKIP  {rel} (harness skills dir missing)")
            continue
        if args.dry_run:
            print(f"DRY   {dest}")
            continue
        try:
            if dest.exists():
                shutil.rmtree(dest)
            # repo-only material (.git, CI, tests, metrics runs, evals) stays
            # out of harness skill dirs — agents need the skill, not its repo
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(
                    ".git", ".github", ".gitignore", ".gitattributes",
                    ".pytest_cache", "__pycache__", "tests", "metrics", "evals",
                ),
            )
            print(f"OK    {dest}")
        except OSError as exc:
            print(f"FAIL  {dest}: {exc}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
