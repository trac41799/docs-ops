# Rules — process, writing, hygiene

## Process principles (5)

1. **One home per fact.** The fact lives in exactly one doc; everything else links. ADRs own decisions, specs own designs, plans own tasks, changelog owns behavior history.
2. **Docs travel with code.** Any behavior change updates the relevant spec/ADR/changelog **in the same MR**.
3. **Decisions before code.** Significant technical choices (framework, contract, schema) get an ADR first, even a short one.
4. **Epics get specs + plans.** Spec issue → plan file → implementation MRs referencing `Closes #N`.
5. **Specs state delivery status.** Every normative spec carries a Delivered-vs-Deferred table and marks unmet requirements inline; a spec is a target, not a claim of shipped state.

## Change-type → required doc update

| Change | Update |
|---|---|
| New behavior/feature | spec issue + `plans/` + `changes/CHANGELOG.md` |
| Architecture/framework/contract decision | new ADR + spec touch if it describes design |
| API surface change | living API contract page (+ CI snapshot if present) |
| Eval/test threshold change | QA thresholds page + run report under `qa/runs/` |
| Methodological review pass | `reviews/` findings, cited from affected specs |
| Diagram | edit the **one** authored source, or the curated generator input — never the generated file |
| Docs site / manifest | edit generator source → regenerate → run docs guards |
| DDL/schema change | ER regenerates from DDL; never edit the ER artifact |
| State channel / transport contract | the architecture page that tables it + its drift guard |

## Writing rules (STE-light)

Full profile: `docs/standards/writing-guide.md`. The eight rules that bind all prose:

1. Imperative mood; start each instruction with a verb.
2. One instruction per sentence; never chain two actions with "and".
3. Condition first: "If X, do Y." — never bury the condition after the action.
4. Active voice, named actor; passive only when the actor is unknown.
5. ≤20 words per sentence; explanations may run longer but open with the conclusion.
6. No contractions ("do not", never "don't").
7. Exact paths and symbol names; never paraphrase a file or identifier.
8. One term per concept — use the glossary term, never a synonym.

**RFC 2119 scope.** Uppercase MUST/SHOULD/MAY is valid only on the repo's allowlisted normative pages (typically specs, decisions, standards). Everywhere else use lowercase or reword. Lowercase "must" in an allowlisted page is *wrong* — it carries no weight.

**BLUF.** Lead every doc and issue body with the conclusion (≤5 lines), then detail. Never open with preamble or history.

## Hygiene

- Diagrams in mermaid (GitLab renders natively); validate before merge.
- No screenshots of code; no duplicated tables across docs (link instead).
- Relative links between docs; no machine-absolute paths in committed prose or fixtures.
- UAT evidence: numbered screenshots + `EVIDENCE.md` per run; latest run replaces older evidence — git history archives the past.
- Keep generated outputs (diagrams, sites) out of hand-edit scope; the drift guards enforce this.

## Anti-patterns to catch in review

- A fact restated in two docs (drift seed).
- An ADR written after the code (post-hoc justification).
- A plan step without real code ("wire up X" with no test named).
- A changelog entry in the MR description only.
- Editing a generated `.mmd`/`.png`/`site/` file instead of its source.
