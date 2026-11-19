# docs-ops

A documentation skill for a small starting structure, audience-aware writing, and optional lifecycle checks.

- **Structure** — an index and writing guide by default; add areas when needed
- **Writing** — ISO 24495-1 plain-language principles, an ASD-STE100 subset, and an audience-aware audit
- **Enforcement** — stdlib checker (CI-safe), optional Vale, drift guards
- **Measurement** — scored health reports with budgets + append-only trends
- **Regression net** — agent-navigation evals that keep the skill usable

Reference implementation: the `tripcomposer` docs tree.

## Install (this machine)

The canonical copy is this repo itself (`~\.agents\skills\docs-ops`). Every
harness on the machine consumes the same Agent-Skills folder format:

```
python scripts/propagate.py            # copy to all harness skills dirs
python scripts/propagate.py --list     # show target state
python scripts/propagate.py --target .claude/skills
```

Targets: `.claude`, `.codex`, `.cursor`, `.copilot`, `.gemini`, `.qwen`,
`.roo`, `.iflow`, `.factory` skills dirs. OpenCode reads `.agents/skills`
natively — no copy needed there.

### New machine / another user

```
git clone <this-repo> ~/.agents/skills/docs-ops
cd ~/.agents/skills/docs-ops
python scripts/propagate.py
```

## Update flow

```
git pull            # in ~/.agents/skills/docs-ops
python scripts/propagate.py
```

Tag releases (`v0.1.0`); the CHANGELOG is the release narrative.

## Use in a repo

| Mode | Command |
|---|---|
| Scaffold | `python scripts/scaffold_docs.py <repo-root> --project Name` |
| Prose gate | `python scripts/check_docs.py --strict --root <repo>` |
| Health report | `python scripts/collect_metrics.py --root <repo>` |
| Agent evals (maintainers) | `python evals/run_evals.py` |

The default scaffold creates only `docs/README.md` and `docs/standards/writing-guide.md`. Use `--full` to create the legacy tree and templates. Neither mode deletes existing files. The writing audit reports findings by default and rewrites only on request.

Per-repo checker config: `docs-ops.json` at the repo root (RFC allowlist,
procedure globs, sentence cap, banned synonyms). Health budgets:
`metrics/budgets.json` (copy into the adopting repo and tune).

## Measuring effectiveness

`collect_metrics.py` answers, with evidence:

1. **Is the starting structure there?** `docs/` and `docs/standards/` present
2. **Do the docs pass the rules?** checker errors/warnings
3. **Do links resolve?** relative markdown link scan
4. **Is the process real?** % of behavior commits (git log) that also touched
   the changelog; ADR/plan/spec counts; Delivered-vs-Deferred table presence
5. **How stale is each area?** days since last touch

Runs are append-only JSON under `metrics/runs/` — commit them in the adopting
repo; the trend is the deliverable. Exit 1 on budget failure, CI-ready.
Details: [`metrics/README.md`](metrics/README.md).

Agent-navigation evals (`evals/`) regression-test the skill itself: a fresh
agent gets only the skill directory and must answer five real docs-lifecycle
questions with correct file citations. Run them after editing `SKILL.md` or
`references/`. Details: [`evals/README.md`](evals/README.md).

## Repo layout

```
SKILL.md            skill router (the only file harnesses load up front)
references/         structure, rules, enforcement, patterns (progressive disclosure)
templates/          ADR, spec-issue, plan, CONTRIBUTING, README index, CHANGELOG
scripts/            scaffold_docs · check_docs · collect_metrics · propagate
metrics/            budgets + trend-run guide
evals/              navigation scenarios + runner (maintainer-facing)
tests/              pytest suite for the scripts (CI)
```

## CI

GitHub Actions runs the pytest suite plus a scaffold → check → collect smoke
on every push. Agent evals are **not** in CI (token cost) — they gate releases.

## License

MIT — see [LICENSE](LICENSE).
