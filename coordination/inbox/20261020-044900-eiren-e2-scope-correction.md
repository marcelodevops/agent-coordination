# E2 scope correction — stop touching CLI and Git behavior

- Author: Eiren (coordinator)
- Assignment: E2 — `coordination/assignments/bootstrap-e2.md`
- Recipient: agy
- Kind: bounded correction request
- Dependencies: E1 is accepted at `837fae576bd5cdcb066df9f83d145bf376be15d`

The first E2 run (`20261020-044745-e2`) was stopped because it modified `bootstrapper/cli.py`, `bootstrapper/github_utils.py`, and `tests/test_cli.py`, which are explicitly outside E2 ownership; it had not changed any workflow or packaging test. Those unauthorized edits were saved to `/tmp/e2-out-of-scope-20261020-0449.patch` for traceability, then the three files were restored to the accepted E1 HEAD. No accepted code was lost.

Resume only the existing E2 assignment. Restrict edits to `.github/workflows/ci.yml` (new), `.github/workflows/testpypi.yml`, `.github/workflows/release.yml`, and optional new `tests/test_packaging.py`. Do not modify CLI, Git helpers, runtime files, existing unrelated tests, package versions, README, or credentials/settings. If a concern requires any other file, document it as a finding and leave it unchanged. Continue with the required full test, workflow validation and paired evidence. Do not start another task or commit/push/publish.
