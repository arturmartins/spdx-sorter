# Ticket 06C — Final verification and branch review

## Assigned model

Use `gpt-5.6-terra` with high reasoning for the independent whole-branch
review. Do not use a Sol model. The controller runs deterministic verification
commands locally before dispatching the review.

## Objective

Verify the complete hardening/publication implementation, review the entire
dirty worktree against `ROADMAP.md` and `docs/plan/`, update status honestly,
and prepare the user handoff without committing or publishing implementation.

## Required verification

- Full pytest suite with real validation extra.
- Ruff format check and lint.
- Strict mypy on production code.
- Independent line >=95% and branch >=90% coverage gates.
- Wheel/sdist build, Twine checks, and clean base-wheel consumer smoke.
- JSON/YAML parsing, full-SHA external action scan, permission/event/secret
  static checks, and `git diff --check`.
- Native Docker build and non-root/read-only/validate smokes if a daemon exists;
  otherwise record the environment limitation without claiming runtime proof.
- Final independent review for correctness, security, maintainability, plan
  compliance, and claims that exceed evidence.

## Completion rules

Fix Critical/Important findings, preserve all user-owned work, do not publish,
and mark phases 5–6 partial until remote settings and a hosted release prove the
exit criteria. Phase 7 remains not started until the user authorizes release.
