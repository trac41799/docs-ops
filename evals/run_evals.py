#!/usr/bin/env python3
"""Run agent-navigation evals against this skill.

A fresh agent gets the skill directory and five docs-lifecycle scenarios.
Grading is deterministic: each scenario lists case-insensitive substrings that
must appear in the answer (file citations and key terms the skill must surface).

Usage:
    python run_evals.py [--skill-dir DIR] [--provider claude|opencode|command]
                        [--command-template CMD] [--scenario ID] [--list] [--runs N]

Providers:
    claude    claude -p <prompt> --output-format text --allowedTools "Read,Glob,Grep"
              (proven on Windows; needs Claude Code CLI + auth)
    opencode  opencode run <prompt>
              (must run OUTSIDE an active opencode session — nesting is refused)
    command   any template containing {prompt}; cwd = skill-dir

Exit 0 when every scenario passes; 1 when any fails; 2 on operational error.
Each run appends JSON to evals/runs/ next to this script.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
PROMPT_PREFIX = """You are verifying whether a documentation-ops skill is usable by a fresh agent.
Read ONLY files inside {skill_dir} (SKILL.md, references/*, templates/*, scripts/*).
Do not modify any file. Do not run any script.
Answer using ONLY what the skill provides. Cite the exact skill file for each claim.
If the skill does not answer something, say "NOT IN SKILL" for that part — do not improvise from your own knowledge.

Scenario: {prompt}
"""

TIMEOUT_S = 240


def load_scenarios(scenario_id: str | None) -> list[dict]:
    all_scenarios = json.loads((EVALS / "scenarios.json").read_text(encoding="utf-8"))
    if scenario_id:
        all_scenarios = [s for s in all_scenarios if s["id"] == scenario_id]
        if not all_scenarios:
            known = [s["id"] for s in json.loads((EVALS / "scenarios.json").read_text(encoding="utf-8"))]
            raise SystemExit(f"unknown scenario {scenario_id!r}; known: {known}")
    return all_scenarios


def run_provider(provider: str, prompt: str, skill_dir: Path, command_template: str | None) -> str:
    if provider == "claude":
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "text",
            "--allowedTools", "Read,Glob,Grep",
        ]
    elif provider == "opencode":
        cmd = ["opencode", "run", prompt]
    elif provider == "command":
        if not command_template or "{prompt}" not in command_template:
            raise SystemExit("error: --command-template must contain {prompt}")
        cmd = shlex.split(command_template.format(prompt=prompt), posix=False)
    else:
        raise SystemExit(f"error: unknown provider {provider!r}")

    r = subprocess.run(
        cmd,
        cwd=str(skill_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT_S,
    )
    if r.returncode != 0:
        raise RuntimeError(f"{provider} exited {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
    return r.stdout


def grade(answer: str, scenario: dict) -> dict:
    low = answer.lower()
    missing = [s for s in scenario["required_substrings"] if s.lower() not in low]
    present = [s for s in scenario["forbidden_substrings"] if s.lower() in low]
    return {
        "passed": not missing and not present,
        "missing_required": missing,
        "forbidden_found": present,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skill-dir", type=Path, default=EVALS.parent)
    ap.add_argument("--provider", default="claude", choices=["claude", "opencode", "command"])
    ap.add_argument("--command-template", default=None)
    ap.add_argument("--scenario", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--runs", type=int, default=1, help="repeat each scenario N times (flakiness check)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    skill_dir = args.skill_dir.resolve()
    if not (skill_dir / "SKILL.md").is_file():
        print(f"error: {skill_dir} has no SKILL.md", file=sys.stderr)
        return 2

    if args.list:
        for s in load_scenarios(None):
            print(f"{s['id']}: {s['prompt'][:80]}…")
        return 0

    scenarios = load_scenarios(args.scenario)
    results: list[dict] = []
    for sc in scenarios:
        for run_idx in range(args.runs):
            prompt = PROMPT_PREFIX.format(skill_dir=skill_dir, prompt=sc["prompt"])
            print(f"--- {sc['id']} (run {run_idx + 1}/{args.runs}) via {args.provider} ---")
            try:
                answer = run_provider(args.provider, prompt, skill_dir, args.command_template)
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                print(f"  ERROR: {exc}")
                results.append({"scenario": sc["id"], "run": run_idx + 1, "passed": False, "error": str(exc)})
                continue
            g = grade(answer, sc)
            print(f"  {'PASS' if g['passed'] else 'FAIL'}"
                  + (f" missing={g['missing_required']}" if g["missing_required"] else "")
                  + (f" forbidden={g['forbidden_found']}" if g["forbidden_found"] else ""))
            results.append({
                "scenario": sc["id"],
                "run": run_idx + 1,
                "passed": g["passed"],
                "missing_required": g["missing_required"],
                "forbidden_found": g["forbidden_found"],
                "answer_chars": len(answer),
            })

    passed = sum(1 for r in results if r["passed"])
    report = {
        "meta": {
            "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "skill_dir": str(skill_dir),
            "provider": args.provider,
            "runs_per_scenario": args.runs,
        },
        "results": results,
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
    }
    runs_dir = EVALS / "runs"
    runs_dir.mkdir(exist_ok=True)
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    out = runs_dir / f"evals-{day}-{args.provider}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\n{passed}/{len(results)} passed — report: {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
