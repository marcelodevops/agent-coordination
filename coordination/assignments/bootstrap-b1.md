> CANCELLED: user removed Copilot on 2026-10-17T23:28:54-03:00. Historical assignment; no longer authorizes any work. Replacement will be issued to Mr.Q after A1 review.

# B1 — usable generated Helm chart
Owner: Copilot. State: ready. Dependencies: none.
Workspace: /Users/mac/ops/worktrees/project-bootstrapper-plan
Owned product files: bootstrapper/templates.py (HELM SECTION ONLY), NEW tests/test_generated_helm.py only.
Goal: fix fullname whitespace causing invalid YAML and the empty default image tag. Use appVersion as the default tag when no image.tag was set, retaining explicit override.
Acceptance: a generated chart passes native helm lint and helm template; default and fullnameOverride metadata names stay valid; default image ends in :1.0.0; explicit tag override is honored. Tests use real helm when available and explain an explicit skip when unavailable, without network or a Kubernetes cluster. Tests may use installed PyYAML; do not change dependencies (coordinator will declare the test requirement). Do not claim deployment readiness of the placeholder image.
Don't change other stack templates or renderer, CLI, composer, agents, presets or pyproject.

## Mandatory inputs
Read /Users/mac/ops/repos/agent-coordination/AGENTS.md, STARTING-POINT.md, coordination/RULES.md and coordination/STATUS.md.
Product plan: /Users/mac/ops/worktrees/project-bootstrapper-plan/docs/superpowers/plans/2026-10-17-bootstrap-product-improvement-plan.md. Product worktree: /Users/mac/ops/worktrees/project-bootstrapper-plan.
You are not alone in the codebase. Do not revert other workers' changes. Do not edit coordinator-owned status, plan.json, or other assignments. Do not commit, push, publish, install/update agents, or modify user secrets. Preserve the source checkout and its untracked uv.lock. No subagents or additional workers.
Use existing configured model. The user explicitly approved execution; no further planning approval is needed for this bounded assignment.
For product tests use /tmp/projboot-execution-venv/bin/python -m pytest. Baseline: 60 tests passed.
Write a failing regression test, capture its expected failure, implement the smallest fix, run covering tests. Record limitations honestly. Do not claim native-client testing from static parsing. Do not broaden into adjacent roadmap tasks.
## Required messages
Create a NEW uniquely named Markdown result in /Users/mac/ops/repos/agent-coordination/coordination/outbox/ and a paired review request in /Users/mac/ops/repos/agent-coordination/coordination/inbox/. Names: YYYYMMDD-HHMMSS-<agent>-<task>-result.md / -review.md using America/Santiago time. Include author, assignment, intended recipient Eiren, kind, dependencies, changed files, verification commands/results, remaining limitations and requested decision. Use relative links to this assignment and between paired messages. Never overwrite existing messages. Finishing the worker process is not coordinator acceptance.
