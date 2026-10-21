# E1 — One Git history and recoverable remote setup

Owner: Mr.Q. Dependency: D2 accepted. Product workspace: `/Users/mac/ops/worktrees/project-bootstrapper-plan`.

Read the approved product plan, central coordination rules/status, and this assignment before editing. Preserve all existing changes, including the uncommitted D1R correction in `bootstrapper/templates.py`, `tests/test_cli.py`, and `tests/test_generated_helm.py`. Do not alter those files. This task is limited to new-repository creation/connection and truthful failure reporting; do not edit release workflows, package versions, credentials, or publication configuration.

## Goal

For a newly created remote repository, make the local generated checkout and remote share one Git history using a normal first push. Do not upload scaffold files as separate GitHub API commits or report success when repository setup, commit, remote configuration, or push failed. Stage only paths from the composed generated-file plan; never stage unrelated pre-existing files.

## Ownership

Own only the minimum needed in `bootstrapper/github_utils.py`, `bootstrapper/cli.py`, `bootstrapper/composer.py` (post-generation Git hooks), plus a new focused `tests/test_git_history.py`. Narrow updates are additionally authorized in `tests/test_cli_first_steps.py` and `tests/test_cli.py` because their `--clone` assertions encode the superseded API-upload/fetch-reconcile workflow; update only those assertions to require normal push success or truthful partial failure. Do not modify other test files or user changes. This is an explicit ownership expansion recorded by the coordinator because the existing assertions are incompatible with the approved E1 acceptance behavior.

## Acceptance

- Add a temporary local bare-remote integration test that creates a generated project, makes the initial commit locally, pushes normally, and proves the local and remote refs point to the same history with the expected generated files.
- Verify unrelated pre-existing files in the worktree do not enter the commit.
- Cover a concrete setup/push failure and prove the CLI reports failure/partial state without claiming the checkout is ready or the remote was connected successfully.
- Preserve existing explicit behavior for `--local`, `--no-git`, `--remote` without `--create`, and refusing an existing remote unless `--force` is selected. Do not imply that `--force` may rewrite remote history.
- Run focused tests, full suite `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`, and `git diff --check`.
- Write NEW paired outbox result/inbox review-request files with commands, results, exact files, exact base commit, and remaining limitations. Do not commit/push product code or call GitHub.

## Coordinator correction scope — 2026-10-20 04:50 -03

E1 is reopened. The accepted implementation still leaves legacy `init` and `create --create` without `--clone` using file-by-file GitHub API commits, contrary to the approved single-history goal. The correction expands the same owned files to ensure all Git-enabled remote creation paths use one normal local commit/push; `--clone` remains accepted as a compatibility flag. `--no-git` creates/selects the remote but skips pushing and must say the remote contents were not inspected. Keep `--force` limited to selecting an existing repository; it never authorizes overwriting remote history. Add regressions for remote refusal before local writes, truthful `--force --no-git` reporting, and local/remote ref equality on legacy init and create without `--clone`. Do not edit release workflows or unrelated files. This supersedes the prior E1 acceptance pending independent re-review and full verification.
