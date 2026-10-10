#!/usr/bin/env python3
"""Deterministic docs prose checker. Stdlib only — safe as a CI gate.

Usage:
    python check_docs.py [--root DIR] [--strict] [paths...]

Config: optional docs-ops.json at the repo root (see README in this skill).
Default checks:
  - RFC 2119 uppercase MUST/SHOULD/MAY only on allowlisted normative globs
  - sentence length on procedure globs (runbooks, plans, AGENTS.md)
  - banned synonym pairs (word-boundary matched), minus exempt globs

Exit 0 when clean (or when not --strict); exit 1 on violations with --strict
or on unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    # templates and CONTRIBUTING quote the keywords as instructions, so they
    # sit on the allowlist — otherwise every scaffolded repo fails its own gate
    "rfc_allowlist": [
        "docs/specs/**",
        "docs/decisions/**",
        "docs/standards/**",
        "docs/architecture/api.md",
        "docs/templates/**",
        "docs/CONTRIBUTING.md",
    ],
    "procedure_globs": ["AGENTS.md", "docs/plans/**", "docs/*.md"],
    "sentence_cap": 20,
    "banned_synonyms": {},
    "synonym_exempt": [],
}

# uppercase keyword as a standalone word; (?<![A-Z]) blocks "MUSTANG"-style tails
RFC_META_RE = re.compile(r"(?<![A-Z])(MUST|SHOULD|MAY)(?![A-Z])")
LOWER_KEYWORD_RE = re.compile(r"\b(must|should|may)\b", re.IGNORECASE)
# split on [.?!] + space/EOL — "e.g."/"i.e." do not end sentences here (no space after.)
SENT_RE = re.compile(r"[^.!?]*[.!?]+")
SYNONYM_RE_TEMPLATE = r"\b{word}\b"

ANSI = {"red": "\x1b[31m", "yellow": "\x1b[33m", "dim": "\x1b[2m", "reset": "\x1b[0m"}


def c(code: str, text: str) -> str:
    return f"{ANSI[code]}{text}{ANSI['reset']}"


def strip_code(text: str) -> list[str]:
    """Return non-code lines with original numbering (1-based)."""
    out: list[str] = []
    in_fence = in_math = False
    for n, line in enumerate(text.splitlines(), 1):
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            out.append("")  # keep line numbering aligned
            continue
        if s.startswith("$$") or s.startswith("\\[") or s.startswith("\\]"):
            in_math = not in_math
            out.append("")
            continue
        if in_fence or in_math or s.startswith("    "):
            out.append("")
            continue
        out.append(line)
    return out


def md_files(root: Path, globs: list[str]) -> set[Path]:
    """Collect .md files for config globs.

    Trailing-`**` semantics changed across Python versions (3.12 vs 3.13+
    pathlib differ), which silently emptied allowlists on older CI images.
    Handle the config's real patterns explicitly instead of relying on
    version-specific `glob("**")` behavior.
    """
    found: set[Path] = set()
    for g in globs:
        g = g.replace("\\", "/")
        try:
            if g.endswith("/**"):
                base = root / g[: -len("/**")]
                if base.is_dir():
                    found.update(p for p in base.rglob("*.md") if p.is_file())
            elif g.endswith("/*.md"):
                base = root / g[: -len("/*.md")]
                if base.is_dir():
                    found.update(p for p in base.glob("*.md") if p.is_file())
            elif "*" not in g and "?" not in g:
                p = root / g
                if p.is_file() and p.suffix == ".md":
                    found.add(p)
            else:
                found.update(p for p in root.glob(g) if p.is_file() and p.suffix == ".md")
        except ValueError:
            print(f"warn: bad glob {g!r}", file=sys.stderr)
    return found


def check_rfc(files: set[Path], root: Path) -> list[str]:
    errors: list[str] = []
    for f in sorted(files):
        rel = f.relative_to(root).as_posix()
        for i, line in enumerate(strip_code(f.read_text(encoding="utf-8-sig", errors="replace")), 1):
            m = RFC_META_RE.search(line)
            if m:
                errors.append(f"{rel}:{i}: uppercase {m.group(1)} outside allowlisted page")
    return errors


def check_sentences(files: set[Path], root: Path, cap: int) -> list[str]:
    errors: list[str] = []
    for f in sorted(files):
        rel = f.relative_to(root).as_posix()
        for i, line in enumerate(strip_code(f.read_text(encoding="utf-8-sig", errors="replace")), 1):
            for sent in SENT_RE.findall(line):
                n = len(sent.split())
                if n > cap:
                    snippet = sent.strip()[:70]
                    errors.append(f"{rel}:{i}: sentence has {n} words (cap {cap}): {snippet}…")
    return errors


def check_synonyms(files: set[Path], root: Path, pairs: dict[str, str], exempt: list[str]) -> list[str]:
    errors: list[str] = []
    exempted = md_files(root, exempt) if exempt else set()
    for term, canon in sorted(pairs.items()):
        rx = re.compile(SYNONYM_RE_TEMPLATE.format(word=re.escape(term)), re.IGNORECASE)
        for f in sorted(files):
            if f in exempted:
                continue
            rel = f.relative_to(root).as_posix()
            for i, line in enumerate(strip_code(f.read_text(encoding="utf-8-sig", errors="replace")), 1):
                if rx.search(line):
                    errors.append(f"{rel}:{i}: term '{term}' — use '{canon}'")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="files/dirs to scan (default: doc surface)")
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default cp1252
    except Exception:
        pass

    root: Path = args.root.resolve()
    cfg = dict(DEFAULT_CONFIG)
    cfg_file = root / "docs-ops.json"
    if cfg_file.is_file():
        try:
            # utf-8-sig strips a Windows-editor BOM; plain utf-8 would raise
            cfg.update(json.loads(cfg_file.read_text(encoding="utf-8-sig")))
        except json.JSONDecodeError as exc:
            print(f"error: {cfg_file}: {exc}", file=sys.stderr)
            return 1

    if args.paths:
        targets = {Path(p).resolve() for p in args.paths}
        files: set[Path] = set()
        for t in targets:
            if t.is_dir():
                files.update(p for p in t.rglob("*.md") if p.is_file())
            elif t.is_file() and t.suffix == ".md":
                files.add(t)
        rfc_targets = files
        proc_targets = files
    else:
        rfc_all = md_files(root, cfg["rfc_allowlist"] + ["**/*.md"])
        allowed = md_files(root, cfg["rfc_allowlist"])
        rfc_targets = rfc_all - allowed
        proc_targets = md_files(root, cfg["procedure_globs"])

    errors: list[str] = []
    warnings: list[str] = []
    errors += check_rfc(rfc_targets, root)
    warnings += check_sentences(proc_targets, root, int(cfg["sentence_cap"]))
    errors += check_synonyms(
        md_files(root, ["**/*.md"]) if cfg["banned_synonyms"] else set(),
        root,
        dict(cfg["banned_synonyms"]),
        list(cfg.get("synonym_exempt", [])),
    )

    for e in errors:
        print(c("red", f"error: {e}"))
    for w in warnings:
        print(c("yellow", f"warn:  {w}"))
    print(c("dim", f"{len(errors)} errors, {len(warnings)} warnings ({root})"))
    if errors and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
