# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-10

### Added
- `docs-ops` skill: Scaffold / Manage / Audit modes over an SDLC-aligned docs tree.
- `scripts/scaffold_docs.py`: idempotent scaffolder (never overwrites content; bootstrap-safe).
- `scripts/check_docs.py`: stdlib prose checker (RFC 2119 placement, sentence cap,
  banned synonyms; `docs-ops.json` config; Windows-BOM tolerant).
- `scripts/collect_metrics.py`: scored docs-health report (structure, prose, links,
  git-derived changelog coverage, staleness) with `metrics/budgets.json` gates and
  append-only trend runs.
- `scripts/propagate.py`: plain-copy propagation to all harness skills dirs, with a
  repo-material ignore list.
- `evals/`: five agent-navigation scenarios + harness-agnostic runner
  (`claude` / `opencode` / `command` providers), deterministic citation grading.
- `tests/`: pytest suite for scaffold, checker, and collector.
- CI: pytest + scaffold→check→collect smoke on every push.
- Docs: README, references (structure / rules / enforcement / patterns), templates
  (ADR, spec-issue, plan, CONTRIBUTING, README index, CHANGELOG, writing-guide seed).
