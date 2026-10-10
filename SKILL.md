---
name: docs-ops
description: Use when scaffolding or bootstrapping a docs/ documentation structure in a repo, creating ADR / spec-issue / plan boilerplate, deciding which docs a code change must update, maintaining documentation lifecycle rules, auditing docs against SDLC conventions, or regenerating generated diagram/site doc layers.
---

# docs-ops — documentation structure & lifecycle

Maintain one SDLC-aligned `docs/` tree per repo: **SDD → planning → build → QA →
review**, with decisions, research, changelog, and generated layers handled as
first-class areas. Reference implementation: `tripcomposer/docs/`.

## Authority order

1. The repo's own `docs/CONTRIBUTING.md` and `docs/standards/writing-guide.md`, if present.
2. This skill's defaults (templates, checklists, checker).

Never add a second writing guide or structure map to a repo that already has one — link instead.

## Modes

| Mode | Trigger signals | Do this |
|---|---|---|
| **Scaffold** | "bootstrap docs", "set up docs structure", "new repo documentation" | Run `scripts/scaffold_docs.py <repo-root>`; it creates the tree and seeds missing files from `templates/`, never overwriting content. Then adapt `docs/README.md` and `CONTRIBUTING.md` to the repo. |
| **Manage** | "which doc do I update", "docs lifecycle", epic/ADR/spec/plan/changelog questions | Read `references/rules.md` (change-type matrix) and `references/patterns.md` (worked flows: ADR, spec issue → plan → MR, diagram routing, site regeneration). |
| **Audit** | "docs hygiene", "audit docs", "docs health", review of a docs-heavy MR | Run `scripts/check_docs.py --strict --root <repo>` for rule violations; run `scripts/collect_metrics.py --root <repo>` for a scored health report with budgets (prose, links, changelog coverage, structure, staleness); walk `references/patterns.md` §8; file gaps as issues. |

## Core rules (full text: `references/rules.md`)

- One home per fact; everything else links to it.
- Docs travel with code — same MR updates spec/ADR/changelog.
- Decisions before code — significant choices get an ADR first.
- Epics get a spec issue + a plan file before implementation.
- Specs carry a Delivered-vs-Deferred table; they are targets, not claims of shipped state.
- Prose: imperative, condition-first, active, ≤20 words, no contractions, exact paths, one term per concept, RFC 2119 keywords only on allowlisted pages, BLUF-first.
- Generated layers (diagrams, sites, C4 output, ER artifacts) are never hand-edited — edit the curated source and regenerate.

## Verify ladder

1. `python scripts/check_docs.py --strict --root <repo>` (config: `docs-ops.json`).
2. Repo-owned docs guards, if present (pytest drift tests for generated layers).
3. Vale, only if the repo already runs it — optional, never the gate.

## Files

- `references/structure.md` — the full area map, per-area contracts, navigation paths, generated-layer table.
- `references/rules.md` — process principles, change-type matrix, writing rules, hygiene, anti-patterns.
- `references/enforcement.md` — checker/Vale/structural/CI ladder, regeneration inventory, freshness-guard gotchas (EOL + machine-root redaction).
- `references/patterns.md` — worked examples: ADR, epic → spec → plan, diagram routing decision tree, site change, audit pass.
- `templates/` — ADR, spec-issue, plan, CONTRIBUTING, docs-README (index), CHANGELOG, writing-guide seed.
- `scripts/scaffold_docs.py` — idempotent scaffolder (`--dry-run`, `--repair`, `--project`).
- `scripts/check_docs.py` — stdlib prose checker (RFC placement, sentence cap, banned synonyms; `docs-ops.json` config).
- `scripts/collect_metrics.py` — scored docs-health report with budgets; append-only trend runs (`metrics/budgets.json`, guide in `metrics/README.md`).
- `scripts/propagate.py` — re-copy this skill into every harness skills dir on the machine (`--list`, `--target`, `--dry-run`).
- `evals/` — maintainer-facing agent-navigation scenarios + runner (`evals/README.md`); not part of adopting-repo CI.
