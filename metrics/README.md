# Metrics — does the docs system actually work?

`scripts/collect_metrics.py` turns the docs conventions into numbers. Run it
against any adopting repo; commit the JSON runs to build a trend line.

## What is measured

| Section | Question it answers | Source |
|---|---|---|
| structure | Is the SDLC tree actually present? | filesystem |
| prose | Do the docs pass the deterministic rule checker? | `check_docs.py` |
| links | Do relative links resolve? | markdown scan |
| process | Do behavior commits touch the changelog? Do ADRs/plans/specs exist? Is the Delivered-vs-Deferred table present? | `git log` (non-merge commits in window) |
| staleness | How stale is each docs area? | `git log -1` per area |
| budgets | Does the repo clear the bar? | `budgets.json` |

## Usage

```
python scripts/collect_metrics.py --root <repo>            # uses metrics/budgets.json
python scripts/collect_metrics.py --root <repo> --out runs/  # choose archive dir
```

Exit 0 = all budgets pass. Exit 1 = at least one budget fails (CI-friendly).

## Budgets (`budgets.json`)

| Key | Meaning |
|---|---|
| `max_prose_errors` | checker errors allowed (0 recommended) |
| `max_broken_links` | broken relative links allowed |
| `min_changelog_coverage_pct` | % of behavior commits that also touched a changelog |
| `max_structure_missing` | missing scaffold areas allowed |
| `code_globs` | which paths make a commit "behavior" |
| `changelog_paths` | accepted changelog locations |
| `window_days` | git history window for process/staleness deltas |

## Trend runs

Each run writes `docs-health-<date>-<sha>.json` under `metrics/runs/`
(override with `--out`). Commit these files in the adopting repo — the trend
is the point. A red budget in one run is a work item, not a reason to delete
the run.

## Interpreting a FAIL

- **changelog coverage** — find `uncovered_subjects` in the JSON: those merges
  changed behavior without a changelog entry. Fix the docs or adjust
  `code_globs` if they over-match.
- **prose errors** — run `check_docs.py --strict --root <repo>` and fix the
  listed lines; extend `docs-ops.json` synonyms only with a glossary basis.
- **broken links** — one-home-per-fact usually collapsed; restore the link.
- **structure missing** — re-run the scaffolder; it only fills gaps.
