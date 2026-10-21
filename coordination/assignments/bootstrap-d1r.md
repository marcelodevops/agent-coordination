# D1R — Helm chart name compatibility correction

Owner: Mr.Q. Dependencies: A3 and C3 accepted. Product workspace: `/Users/mac/ops/worktrees/project-bootstrapper-plan`.

Read central rules/status and the approved product plan before editing. This is a bounded correction to the independent PR #7 review finding recorded in `coordination/STATUS.md` (2026-10-20T03:40:59-03:00): shared project-name validation accepts uppercase, underscore, dot, and accented Latin letters, while Helm `Chart.yaml` currently receives the raw project name. Examples `My_App` and `café` are invalid Helm chart names.

## Goal

Ensure every project name accepted by the shared CLI contract generates valid Helm chart metadata when the Helm profile is selected, while preserving the project directory name and behavior of non-Helm profiles. Choose the smallest user-understandable implementation; avoid unrelated changes.

## Ownership

Own only the minimum required in `bootstrapper/templates.py`, the CLI/composition validation path if genuinely required, README if behavior needs explanation, and focused generated Helm/CLI tests. Preserve all accepted work, especially D2. Do not alter release workflows, git behavior, package version, or unrelated tests.

## Acceptance

- Add behavioral regressions for valid simple names and representative accepted-but-invalid-for-Helm names (`My_App`, `café`, and a dotted name), exercising actual generated `Chart.yaml` output.
- Verify generated chart metadata meets Helm's chart name constraints; use native `helm lint` if installed and report an explicit skip if not. Do not claim cluster deployment.
- Ensure project directory and non-Helm profile identity remain unchanged.
- Run focused relevant tests, full suite `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`, and `git diff --check`.
- Write NEW paired result/review-request messages with actual commands/results, exact files and revision (no commit/push).

Do not broaden this correction into general naming redesign. If a product ambiguity genuinely blocks the minimal compatible behavior, document the evidence in a new inbox blocker.
