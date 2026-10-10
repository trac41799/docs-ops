# docs/ structure — the SDLC spine

One tree, five phases in order: **SDD → planning → build → QA → review**.
Decisions and research feed the specs; revisions and changelog record outcomes.
The reference implementation lives in `tripcomposer/docs/` (repo `.agents/skills/trip-docs`
is its enforcement checker).

## Area map

| Directory | Phase | What it holds |
|---|---|---|
| `docs/specs/` | SDD | Design contracts. One build-ready source of truth per domain (e.g. `deep-spec.md`); per-epic lean specs live as tracker issues, not files |
| `docs/plans/` | Planning | One plan per epic, `YYYY-MM-DD-<epic-slug>.md`, writing-plans format |
| `docs/standards/` | Everywhere | The writing guide (STE profile + RFC 2119 allowlist). One home for prose rules |
| `docs/decisions/` | Decision records | ADRs, sequential `ADR-####-<slug>.md`, status Proposed → Accepted → Superseded |
| `docs/architecture/` | Design | Architecture docs (numbered narrative series), living API contract page, glossary, `diagrams/` (generated), `site/` (generated) |
| `docs/qa/` | QA | Testing strategy, thresholds, `runs/` (dated run reports), `evidence/` (latest-run-only screenshots + EVIDENCE.md) |
| `docs/reviews/` | Review | Grilling/audit artifacts — findings + dispositions, cited by the specs they shaped |
| `docs/research/` | Research | Primary-source notes that feed specs and reviews |
| `docs/changes/` | Change log | `CHANGELOG.md` — keep-a-changelog, updated per behavior merge |
| `docs/revisions/` | Change record | Per-change tech + plain-English records |
| `docs/templates/` | — | ADR, spec-issue, plan templates |
| `docs/` root | Ops runbooks | Environment/deploy runbooks (e.g. `DOCKER.md`, `DEPLOY-AZURE.md`) — procedure-glob targets |
| `docs/README.md` | Index | The navigation table above, kept in sync by CI (`test_docs_site.py`-style guards where present) |
| `docs/CONTRIBUTING.md` | Hygiene | Process rules; defers wording to the writing guide |

## Per-area contracts

- **ADR** — ≤400 words; Context / Decision / Consequences; one decision each; the `Status` line is the lifecycle.
- **Spec issue** — lean, ≤2000 tokens, BLUF first; Design / Plan / Test / Alignment sections; RFC 2119 keywords allowed here.
- **Plan** — mandatory header (Goal, Architecture, Tech Stack, Spec link, Global Constraints); each task carries Files / Interfaces and a red → green → refactor checkbox sequence; no placeholders.
- **QA evidence** — latest run only per feature; git history is the archive; the dated report goes to `qa/runs/`.
- **Changelog** — one entry per merge that changes behavior.

## Navigation paths

- New reader: `docs/README.md` → build-ready spec → `qa/` strategy.
- Changing architecture: governing ADR → `CONTRIBUTING.md` → the curated source of the diagram you touch.
- Implementing an epic: spec issue → `plans/` → branch → TDD → MR with `Closes #N`.

## Generated layers (never hand-edit)

| Layer | Typical location | Source |
|---|---|---|
| Diagrams | `architecture/diagrams/*.mmd|*.png` | code/DDL renderers or curated cluster scripts |
| Docs site | `architecture/site/` or `site/` | site generator (manifest + templates) |
| C4 output | `site-likec4/` (often gitignored) | authored `architecture.c4` model |
| ER diagrams | with diagrams | the DDL files themselves |

If a file is under a generated directory, find its curated source first. Editing the output is overwritten by the next run and breaks the drift guards.

## Authority order

1. The repo's own `docs/CONTRIBUTING.md` + `docs/standards/writing-guide.md` (if present).
2. This skill's defaults (templates, scaffold, checklists).
Never introduce a second writing guide or a second structure map inside a repo that already has one.
