# Patterns — worked examples

## 1. New decision → ADR

1. Pick the next number: highest existing `ADR-####` + 1.
2. Copy `templates/ADR-template.md` → `docs/decisions/ADR-####-<slug>.md`.
3. Fill Context (options + constraints), Decision (named components/contracts), Consequences (positive + trade-offs + supersedes link).
4. Status `Proposed`; flip to `Accepted` when the decision lands (edit in place, no new file).
5. If the decision changes design prose, touch the spec in the same MR (process rule 2).

## 2. New epic → spec issue → plan → MRs

1. File the lean spec from `templates/spec-issue-template.md` (BLUF ≤5 lines, ≤2000 tokens).
2. Grill the spec at the level of unresolved invariants (idea → UX → design → low-level) *before* planning; record holds in the issue.
3. Write `docs/plans/YYYY-MM-DD-<slug>.md` from `templates/plan-template.md` — tasks with real failing tests, no placeholders.
4. Implement task-by-task; each MR ticks plan checkboxes and references `Closes #N` on the epic issue.

## 3. Behavior change → changelog

Merge that changes user-visible or contract behavior → add the entry under
`changes/CHANGELOG.md` `Unreleased` in the same MR. No separate "changelog MR".

## 4. API surface change

1. Edit the living contract page in `architecture/` (source of truth).
2. Regenerate the snapshot if the repo has a CI-validated one.
3. Point the implementation MR at the contract diff — the contract lands first or with the code, never after.

## 5. Diagram routing (decision tree)

```
Is the diagram produced by a generator from code/DDL/config?
├─ Yes → edit the generator input (code, DDL, curated cluster) → rerun → commit outputs + source together
└─ No (authored) → find its ONE authored home (spec section, ADR body, architecture page)
                   → edit there → if a PNG mirror exists, regenerate it from the source
```
Search for the mermaid block title before editing; two copies of the same diagram is a process bug — collapse to one and link.

## 6. Docs site / manifest change

1. Edit the site generator's page tree / manifest (data), not the emitted HTML.
2. Rerun the generator.
3. Run the repo's docs-site + diagram guards (tripcomposer: `test_docs_site.py`, `test_likec4.py`, `test_loop_flows.py`).
4. If a new page needs a code quicklink or C4 badge, add it in the manifest so the guard can see it.

## 7. Repo with generated layers → scaffold guards together

Scaffolding a repo that will generate diagrams/sites? Create in the same pass:
- `diagrams/` output dir (gitignore PNGs if the repo prefers network-free CI),
- the generator script stub,
- the drift guard test — a generated layer without a guard will rot.

`scaffold_docs.py` creates the output dir; the guard is repo-specific code — add it when the first generator lands, not before (YAGNI), and record the obligation in the repo's `CONTRIBUTING.md`.

## 8. Docs audit pass

1. Run `check_docs.py --strict` — fix real violations; extend synonyms only with a glossary basis.
2. Walk the change-type matrix against the last N merges; file missing changelog/ADR/spec touches as follow-up issues.
3. Check authority order: any second writing guide or structure map gets collapsed into the one home.
4. Verify no committed prose cites machine-absolute paths; verify evidence dirs hold latest-run-only.
