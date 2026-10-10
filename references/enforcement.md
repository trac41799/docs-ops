# Enforcement — ladders, regeneration, CI

Docs hygiene is enforced by deterministic tools, not by hope. The ladder, strongest first:

## L1 — deterministic prose checker

`scripts/check_docs.py` (stdlib, zero deps) — the portable version of the repo-local
`trip-docs` checker. It enforces:

- RFC 2119 keyword placement (uppercase only on allowlisted normative globs).
- Sentence length on procedure globs (runbooks, plans, AGENTS.md) — cap from config.
- Banned synonym pairs (e.g. `flow = pipeline`) with word-boundary matching,
  configurable per repo via `docs-ops.json`:

```json
{
  "rfc_allowlist": ["docs/specs/**", "docs/decisions/**", "docs/standards/**"],
  "procedure_globs": ["AGENTS.md", "docs/plans/**", "docs/*.md"],
  "sentence_cap": 20,
  "banned_synonyms": { "flow": "pipeline", "document": "doc" },
  "synonym_exempt": ["**/CHANGELOG.md"]
}
```

Run: `python scripts/check_docs.py --strict --root <repo>` (paths override the defaults).
Exit 1 on any violation; the CI job uses `--strict`.

## L2 — Vale (optional, local)

Vale with a no-contractions style gives richer prose feedback. Keep it **local or a
separate CI job** — it needs a binary download; the L1 checker stays the zero-dep gate.
Seed a `.vale.ini` + one `styles/` style only if the team actually runs Vale.

## L3 — structural guards (repo-owned)

Repos with generated doc layers add pytest-style guards, e.g. tripcomposer's
`test_docs_site.py` (site ↔ code drift), `test_likec4.py` (C4 ↔ graph drift),
`test_loop_flows.py` (graph ↔ view drift). When scaffolding a repo with generated
layers, create the guard *with* the generator — a generated layer without a drift
guard will rot.

## L4 — CI wiring

```yaml
doc-standards:
  stage: lint
  script:
    - python .agents/skills/docs-ops/scripts/check_docs.py --strict --root .
```

Keep the job stdlib-only and parallel-safe. `--strict` is for CI; locally default to
warnings so authors can iterate.

## Regeneration inventory

| Artifact | Edit this | Never this |
|---|---|---|
| Authored mermaid (deep-spec, ADRs) | the markdown containing it | the rendered PNG |
| Code-derived diagrams | the code/curated cluster script → rerun generator | the `.mmd`/`.png` output |
| ER diagram | the DDL files | the ER artifact |
| Docs site pages | site generator source (manifest/templates) → rerun | committed HTML output |
| C4 model | the authored `.c4` source | the exported site |
| API contract snapshot | the living contract page (source of truth) | the snapshot |

Regeneration needs network in some setups (mermaid→PNG services); document the
fallback in the repo's own docs, do not invent per-run workarounds.

## Freshness-guard gotchas (learned the hard way)

1. **Normalize EOL before comparison.** Cross-OS checkouts flip `\n`/`\r\n`; a raw
   byte compare fails on content that is identical. Normalize both sides in the guard.
2. **Redact machine-local roots.** Baked absolute paths (editor quicklinks, site
   roots) differ per checkout; normalize only the *current* machine root out of the
   comparison — never all `C:\...` strings (false negatives).
3. **Simulate CI in a fake root.** Before claiming a guard is CI-safe, run it once
   under a path like `/builds/<group>/<repo>` to catch baked-root dependencies.

## L5 — health budgets (trend measurement)

Gates stop the bleeding; budgets prove the system works. `scripts/collect_metrics.py`
scores an adopting repo on five axes — structure presence, prose-checker errors,
broken relative links, git-derived process coverage (did behavior commits touch
the changelog; do ADRs/plans/specs exist), and per-area staleness — then evaluates
`metrics/budgets.json`. Exit 1 on budget failure makes it CI-ready; each run writes
an append-only JSON under `metrics/runs/` so the trend line is the deliverable.
Red is a work item, not a reason to delete the run. Full guide: `metrics/README.md`.

Skill maintainers (not adopting repos) additionally run `evals/run_evals.py` after
edits to `SKILL.md` or `references/` — five agent-navigation scenarios graded on
deterministic citations. See `evals/README.md`.
