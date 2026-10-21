# E2 — CI, installed artifacts and publication gates

Owner: agy. Dependency: E1 correction accepted and integrated at `cf6410387f2c4dcce550a2e25589aeab6d01299d` (source tree tested in isolated commit `330cd0e7bb991ae733d86367610e37cddd03b57a`). Product workspace: `/Users/mac/ops/worktrees/project-bootstrapper-plan`.

Read the approved product plan, central coordination instructions/status, E1 implementation, current workflows, packaging metadata, tests and README before editing. Preserve all existing changes and keep task commits isolated.

## Goal

Make pull requests validate the source and distributable artifacts, prepare an exact reviewed revision for TestPyPI, and ensure production release publishing uses the configured Trusted Publishing route only after build and smoke gates pass.

## Ownership

Own `.github/workflows/ci.yml` (new), `.github/workflows/testpypi.yml`, `.github/workflows/release.yml`, and only new focused `tests/test_packaging.py` if source-side checks are needed. Do not modify package version/metadata, runtime code, README, credentials, repository/environment settings, or unrelated workflows. Do not trigger TestPyPI or production publishing, create tags, or commit/push.

## Required behavior

- Add PR and main-branch CI with source tests, build of both wheel and sdist, `twine check`, and installed-wheel verification from outside the checkout.
- Exercise CLI help and first-use generation for representative supported profiles from the installed wheel, running the relevant native check where local dependencies are already available or can be installed safely within the workflow. Keep the full source suite as a required gate; do not report unsupported live integrations as verified.
- TestPyPI remains an explicit manual workflow for a reviewed revision. Build and validate artifacts before upload, retain and publish the exact validated artifacts, use OIDC Trusted Publishing, and fail if expected artifacts are absent. Do not infer successful OIDC configuration from workflow source.
- Production release workflow is tag-triggered only. Before publishing, check out the tag's exact source, run the full test/build/metadata/installed-wheel and representative first-use gates, verify tag/version agreement, and publish the resulting distributions through PyPI Trusted Publishing with `id-token: write`; remove the long-lived `PYPI_API_TOKEN` dependency. Publish only after every build/check job succeeds.
- Never use a mutable latest release artifact or a separate rebuild after validation for publishing. Keep package provenance attributable to the checked-out tag and build.
- Keep CI understandable and narrowly scoped. Use pinned action versions consistent with repository practice; avoid adding unrelated security scans or infrastructure.

## Verification and handoff

Run focused workflow/package checks where feasible and the full suite `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`; validate workflow YAML and ensure the workflows reference valid commands/files. Use `git diff --check`. Do not claim GitHub-hosted CI or Trusted Publishing setup succeeded without live evidence.

Write NEW paired outbox result and inbox review-request files with exact commands/results, files, base revision, workflow behavior and limitations. Do not edit `plan.json` or `STATUS.md`; Eiren owns acceptance and dispatch. Do not commit, push, publish, change credentials/settings, or start other workers.
