# A1 — canonical output collision preflight
Owner: Mr.Q (qodercli). State: ready. Dependencies: none.
Workspace: /Users/mac/ops/worktrees/project-bootstrapper-plan
Owned product files: bootstrapper/cli.py, bootstrapper/composer.py, NEW tests/test_output_path_contract.py only.
Goal: reject aliases of the same output destination and file/ancestor conflicts before writing anything.
Reproduce --prompts-file ./README.md overwriting README, and --prompts-file src colliding with Python's src directory. Test rendered path collisions too where applicable. Preserve containment/symlink protections and existing API signatures.
Acceptance: both cases produce a clear CLI validation error and no target files; no differing rendered keys silently overwrite each other; all baseline tests and new path tests pass. Don't implement staging/atomic disk recovery yet (A3). Don't touch templates.py, agents.py, presets.py, pyproject.toml.

## Mandatory inputs
Read /Users/mac/ops/repos/agent-coordination/AGENTS.md, STARTING-POINT.md, coordination/RULES.md and coordination/STATUS.md.
Product plan: /Users/mac/ops/worktrees/project-bootstrapper-plan/docs/superpowers/plans/2026-10-17-bootstrap-product-improvement-plan.md. Product worktree: /Users/mac/ops/worktrees/project-bootstrapper-plan.
You are not alone in the codebase. Do not revert other workers' changes. Do not edit coordinator-owned status, plan.json, or other assignments. Do not commit, push, publish, install/update agents, or modify user secrets. Preserve the source checkout and its untracked uv.lock. No subagents or additional workers.
Use existing configured model. The user explicitly approved execution; no further planning approval is needed for this bounded assignment.
For product tests use /tmp/projboot-execution-venv/bin/python -m pytest. Baseline: 60 tests passed.
Write a failing regression test, capture its expected failure, implement the smallest fix, run covering tests. Record limitations honestly. Do not claim native-client testing from static parsing. Do not broaden into adjacent roadmap tasks.
## Required messages
Create a NEW uniquely named Markdown result in /Users/mac/ops/repos/agent-coordination/coordination/outbox/ and a paired review request in /Users/mac/ops/repos/agent-coordination/coordination/inbox/. Names: YYYYMMDD-HHMMSS-<agent>-<task>-result.md / -review.md using America/Santiago time. Include author, assignment, intended recipient Eiren, kind, dependencies, changed files, verification commands/results, remaining limitations and requested decision. Use relative links to this assignment and between paired messages. Never overwrite existing messages. Finishing the worker process is not coordinator acceptance.
