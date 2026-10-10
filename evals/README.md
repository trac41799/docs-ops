# Evals — can a fresh agent actually use this skill?

Navigation evals for the **skill itself** (maintainer-facing — adopting repos do
not run these). A fresh agent context receives only the skill directory and
five docs-lifecycle scenarios drawn from real work questions. Grading is
deterministic: the answer must cite the skill files that define each rule.

## Run

```
python evals/run_evals.py                          # claude provider, all scenarios
python evals/run_evals.py --provider command --command-template "opencode run \"{prompt}\""
python evals/run_evals.py --scenario api-change-routing --runs 3
python evals/run_evals.py --list
```

| Provider | Requirements |
|---|---|
| `claude` (default) | Claude Code CLI + auth; uses `claude -p --allowedTools "Read,Glob,Grep"` |
| `opencode` | Run **outside** an active opencode session (nesting is refused) |
| `command` | Any CLI template containing `{prompt}`; cwd is the skill dir |

## When to run

- After any edit to `SKILL.md` or `references/` — the scenarios are the
  regression net for navigability. If a citation breaks, the skill got worse.
- Before tagging a release.

## Reading results

Each run appends `evals/runs/evals-<ts>-<provider>.json`. A FAIL lists
`missing_required` substrings — the concepts the answer failed to surface.
`--runs N` repeats each scenario to expose flaky phrasings; treat any
non-100% as a gap in the skill's wording, not the agent.

Evals cost tokens (one agent call per scenario per run). They are never part
of the adopting repo's CI — only of this repo's release checklist.
