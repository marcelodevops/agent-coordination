# D1 — side-effect-free project plan and preview

Owner: Mr.Q (qodercli). Dependencies: A3 and C3 accepted. Product workspace: `/Users/mac/ops/worktrees/project-bootstrapper-plan`.

Read the approved product plan at `docs/superpowers/plans/2026-10-17-bootstrap-product-improvement-plan.md`, central `AGENTS.md`, `STARTING-POINT.md`, `coordination/RULES.md`, `coordination/STATUS.md`, and current CLI/composer implementation before changing code.

## Goal

Add a CLI preview that shows the same fully composed project paths/content inputs and selected requirements/actions as generation, without writing files or invoking side effects. Keep existing CLI behavior and public APIs compatible unless the plan explicitly requires otherwise.

## Ownership

Own only the minimum needed in `bootstrapper/cli.py`, `bootstrapper/composer.py`, and NEW or directly relevant CLI/composition tests. Coordinate any existing test-file edits with current repository state; do not overwrite or revert other workers' changes. No README, templates, release workflow, dashboard, or unrelated cleanup.

## Required behavior

- Preview uses the same resolved options and composition result as actual generation so its listed paths match generation for identical inputs.
- Preview reports final file/directory layout, selected tools/integrations, and requested post-generation actions/requirements clearly.
- Preview performs no filesystem writes, Git initialization/commit/remote operations, Graphify invocation, GitHub/network access, or dependency installation.
- Do not claim a requirement or verification succeeded merely because it was selected or described. Make preview output distinguish selected, required, and not executed.
- Invalid inputs and output collisions fail before side effects.
- Keep the implementation small and within existing CLI structure; do not add a framework or dependencies.

## Verification and handoff

Add failing behavior tests before implementation. Cover representative options and compare preview paths with generated paths for identical arguments. Prove preview leaves its target absent/unchanged and does not invoke hooks or external tools. Run the focused tests and full product suite with `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`, plus `git diff --check`.

Write NEW paired timestamped result and review-request files in central `coordination/outbox/` and `coordination/inbox/` using America/Santiago timestamps. Include exact files, commands/results, reviewed revision if any, limitations, and relative links. Do not edit `plan.json` or `STATUS.md`; Eiren owns acceptance and dispatch. Do not commit, push, publish, or start another agent. If the requirement cannot be met without a product decision, document the concrete ambiguity and stop that task.
