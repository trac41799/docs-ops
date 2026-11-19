---
name: docs-ops
description: Use when scaffolding or bootstrapping a docs/ documentation structure in a repo, creating ADR / spec-issue / plan boilerplate, deciding which docs a code change must update, maintaining documentation lifecycle rules, auditing docs against SDLC conventions, or regenerating generated diagram/site doc layers.
---

# docs-ops — documentation structure & lifecycle

Keep documentation proportionate to the project. Start small and create areas, templates, and process records when they serve a real need.

## Authority order

1. The repo's own `docs/CONTRIBUTING.md` and `docs/standards/writing-guide.md`, if present.
2. This skill's defaults (templates, checklists, checker).

Never add a second writing guide or structure map to a repo that already has one — link instead.

## Modes

| Mode | Trigger signals | Do this |
|---|---|---|
| **Scaffold** | "bootstrap docs", "set up docs structure", "new repo documentation" | Run `scripts/scaffold_docs.py <repo-root>`; it creates the tree and seeds missing files from `templates/`, never overwriting content. Then adapt the index and writing guide. Use `--full` only when the full legacy tree is useful. |
| **Writing** | "audit writing", "remove AI writing", "make this concise" | Read `references/writing.md`; audit by default and edit only when requested. |
| **Manage** | "which doc do I update", "docs lifecycle", epic/ADR/spec/plan/changelog questions | Read `references/rules.md` (change-type matrix) and `references/patterns.md` (worked flows: ADR, spec issue → plan → MR, diagram routing, site regeneration). |
| **Audit** | "docs hygiene", "audit docs", "docs health", review of a docs-heavy MR | Run `scripts/check_docs.py --strict --root <repo>` for rule violations; run `scripts/collect_metrics.py --root <repo>` for a scored health report with budgets (prose, links, changelog coverage, structure, staleness); walk `references/patterns.md` §8; file gaps as issues. |

## Core rules

- Keep one home per fact and update affected documentation with the change.
- Create decisions, specs, plans, and evidence when their value justifies them; follow existing project requirements.
- Match writing to the reader and register. The writing guide owns project prose rules.
- Edit generated material at its source and regenerate it.

## Verify ladder

1. `python scripts/check_docs.py --strict --root <repo>` (config: `docs-ops.json`).
2. Repo-owned docs guards, if present (pytest drift tests for generated layers).
3. Vale, only if the repo already runs it — optional, never the gate.

## Files

- `references/writing.md` — audience-aware concise writing and AI-pattern audit.
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
