# D2 — honest checks and first steps

Owner: agy. Dependency: D1 accepted at `d43efee11d6c4ce9dce0e815d583690dcac32c3d`. Product workspace: `/Users/mac/ops/worktrees/project-bootstrapper-plan`.

Read the approved product plan (`docs/superpowers/plans/2026-10-17-bootstrap-product-improvement-plan.md`), central `AGENTS.md`, `STARTING-POINT.md`, `coordination/RULES.md`, `coordination/STATUS.md`, D1 preview implementation, current generated starter files and README before editing.

## Goal

Make `projboot create` leave the user with concise, actionable first steps and explicit user-runnable checks that match the selected scaffold. Clearly separate what was generated/configured, what hooks actually ran, what is merely a next step, and anything still unverified.

## Ownership

Own only the minimum needed in `bootstrapper/cli.py`, `README.md`, and NEW focused CLI tests. Preserve the accepted D1 implementation and other existing changes. No template redesign, Git lifecycle work, release workflow, dependency installation, network calls, or unrelated cleanup. Do not add a separate check subcommand or automatically run generated project commands; keep this task to accurate post-generation guidance and status reporting.

## Required behavior

- After successful `create`, print a short first-steps summary with commands appropriate to the selected language/profile and options. Include useful user-run checks supported by the generated files (for example, Python tests/build, TypeScript checks, Helm lint where applicable).
- Derive guidance from actual selected/composed content where practical; do not give commands for files or tools absent from that scaffold. Keep Rails labeled as experimental per existing product documentation.
- Clearly label user-run commands as not executed. Report hook outcomes based on actual results; missing tools or skipped hooks must remain pending/not run, never success.
- Never imply dependencies were installed, a generated application was built or tested, an assistant client loaded its overlay, GitHub was verified, or Graphify completed unless that exact check actually ran and succeeded.
- Update the README quickstart/preview guidance so it matches the CLI and current verified support boundaries; preserve unrelated documentation.
- Tests must cover representative supported and non-supported/experimental profiles, selected options, accurate status language, and the absence of claims that checks ran when they did not. Keep verification local and offline.

## Verification and handoff

Add behavioral tests first. Run focused D2 tests, the full suite with `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`, and `git diff --check`. Include actual commands/results and exact changed files/revision in NEW paired result and review-request messages in central `coordination/outbox/` and `coordination/inbox/` using America/Santiago timestamps. Do not edit `plan.json` or `STATUS.md`; Eiren owns review, acceptance, and later dispatch. Do not commit, push, publish, or start other workers. If a concrete product ambiguity blocks the bounded work, document the evidence and stop only that task.
