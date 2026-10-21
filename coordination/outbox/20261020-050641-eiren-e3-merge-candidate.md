# E3 merge and TestPyPI candidate preparation

- Author: Eiren
- Intended recipient: coordinator plan and STATUS
- Assignment: E3 — `coordination/assignments/bootstrap-e3.md`
- Kind: integration and candidate evidence
- Product: `marcelodevops/agent-bootstrap`

## Merged E2/E3 workflow branch

PR #7 is merged. Its branch head was `c69e531aa7a5af132745065f6cd1dea459696074`; hosted CI `verify` passed; the independent E3 reviewer found no blocker. GitHub merge commit on `main`: `93b3a82111472e6d3525da4aea10d02dd4150894`. Branch protection endpoint returned 404 (main is not protected). No release action occurred.

## Candidate version

Checked the live JSON indexes directly: PyPI latest/existing version is `0.1.0`; TestPyPI has no project record (404). Exact candidate `0.1.1rc1` returned 404 from both `https://pypi.org/pypi/agent-bootstrap/0.1.1rc1/json` and `https://test.pypi.org/pypi/agent-bootstrap/0.1.1rc1/json`; PEP 440 parsing succeeded. Independent read-only reviewer confirmed the only version source is `bootstrapper.__version__`, that package metadata and the stable tag check use it, and that `bootstrapper/templates.py`'s separate generated-project `0.1.0` is unrelated.

Created isolated worktree `/Users/mac/ops/worktrees/agent-bootstrap-testpypi-candidate` at `origin/main` and changed only `bootstrapper/__init__.py` from `0.1.0` to `0.1.1rc1`. Preserved unrelated dirty changes found in `/Users/mac/ops/worktrees/project-bootstrapper-plan` (`bootstrapper/cli.py`, `tests/test_cli_first_steps.py`, and untracked `uv.lock`); they are not in the candidate worktree or commit.

Candidate source commit: `4d807f439ef9c4c7a6b2778ee878be3214d91a22`, branch `release/testpypi-rc-0.1.1rc1`, PR #9: https://github.com/marcelodevops/agent-bootstrap/pull/9. PR #9 is OPEN, mergeable, and its hosted CI `verify` is queued. No TestPyPI workflow has run.

Local candidate revision validation:

- Full tests: 218 passed in 25.22s.
- actionlint and PyYAML parsing of CI/TestPyPI/release workflows passed; diff check clean.
- Built wheel and sdist; `twine check` passed.
- Installed wheel outside source; both CLI help commands passed; generated Python starter installed and tests passed (2 passed).
- Wheel SHA-256: `73f4d1d3bee1b47f250aafff2649acd9001b6fadb436e82efab54daa73eb633f`.
- Sdist SHA-256: `c45fb2fdbe866ed20f9c8cfe367046a199bb872b54c21940613a8b2e496e3812`.

These are local validation artifacts only. Next gates: wait for PR #9 hosted CI; if it passes, merge under the existing delegation. Then dispatch `.github/workflows/testpypi.yml` using the exact merged full SHA, verify the uploaded candidate can be installed from TestPyPI in a disposable environment with dependencies installed separately from production PyPI, and perform final integrated E3 review. Do not publish stable until candidate installation and all gates pass.
