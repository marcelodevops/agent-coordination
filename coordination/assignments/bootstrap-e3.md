# E3 — Integrated review, conflict resolution and release evidence

Owner: Eiren. Dependency: E2 accepted and pushed at `e8b14fdd41806c8bcc02e0fbd0c64dcab3cb96e1`. Product worktree: `/Users/mac/ops/worktrees/project-bootstrapper-plan`; PR #7 in `marcelodevops/agent-bootstrap`.

## Goal

Review the exact integrated PR against the approved product plan, resolve its `main` conflict while preserving correct current documentation, independently verify the resulting source, and document the evidence and remaining hosted/release gates.

## Ownership

Coordinator-owned integration/review only: resolve current `README.md` conflict and create an integration commit on the existing PR branch if the result passes review. Preserve all approved task commits and unrelated state. Do not rewrite history, force-push, merge the PR while hosted checks/reviews are absent, change package version, configure credentials/environments, trigger TestPyPI or production publication, or create release tags in E3.

## Acceptance

- Inspect the complete PR diff and README ancestry; retain relevant main-side documentation while preserving accurate claims established by accepted product work.
- Independently review the integrated source/workflow behavior and run full source tests, workflow lint/YAML validation, package build and metadata checks, installed-wheel smoke and representative generated-profile checks where dependencies are available, and `git diff --check`.
- Record exact source revision, commands/results, artifact hashes where applicable, limitations, and the unresolved GitHub review/check/OIDC gates in paired coordinator evidence.
- Push only reviewed commits by fast-forward to the existing PR branch. Obtain hosted required checks and independent PR review before merging; continue the approved TestPyPI → candidate verification → production sequence only after each gate passes.

Do not edit `plan.json` or central `STATUS.md` until coordinator acceptance; Eiren owns that record after review.
