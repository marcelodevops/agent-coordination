# Stable 0.1.1 prepared; production publisher gate remains

- Author: Eiren
- Assignment: `coordination/assignments/bootstrap-e3.md`
- Recipient: coordinator/reviewer
- Kind: stable-release preparation result
- Dependencies: TestPyPI RC2 published and exact install verified.
- Requested decision: accept stable source preparation; configure PyPI Trusted Publishing before tag/release.

## Evidence

- Stable version commit `e52957704396ab26d127cd991736ce751a9ceb13` changes only `bootstrapper.__version__` from `0.1.1rc2` to `0.1.1`. Independent reviewer confirmed it is valid stable PEP 440, based on the RC2-verified tree, with no commit blocker.
- PR #14 `verify` run `39530345572` passed; PR merged to main as `19e04963bf52c597672f2ee1b4e27febc86a78aa`.
- Exact production PyPI version endpoint `/pypi/agent-bootstrap/0.1.1/json` was HTTP 404; production currently has only 0.1.0. No stable tag exists locally or remotely as checked before release preparation.
- Stable source suite: 215 passed in 16.90s. Wheel and sdist built; `twine check` passed both. Stable wheel installed outside source checkout; version 0.1.1 and both CLI entrypoints verified. Generated Python project installed separately and its tests passed (2 passed).
- Artifact parity against the actual TestPyPI RC2 wheel and sdist passed. After replacing `0.1.1rc2` with `0.1.1`, all contents match. Expected version-dependent differences are `bootstrapper/__init__.py`, wheel `METADATA`, wheel `RECORD` hashes/sizes, and sdist `PKG-INFO` metadata files.
- Local stable artifact SHA-256: wheel `01099115ac485edf6289171c0b7cde8bbe01ccf4da0ca3d18d6a8b3b8ed65bf9`; sdist `dd0918ff2da504427cc7c8c8a01dbda661df3cb426dd95ffd5a4ce8dee3c56ec`.
- Release workflow `.github/workflows/release.yml` is tag-triggered. It requires a `vX.Y.Z` tag whose commit is an ancestor of main and whose package version matches the tag, then runs tests, build, twine, and installed-wheel/generated-project checks. Publish uses `pypa/gh-action-pypi-publish@v1.12.3`, OIDC, and GitHub environment `pypi`.

## Genuine account-configuration dependency

The user confirmed TestPyPI Trusted Publishing was configured; this was proven by successful RC2 upload. Production PyPI Trusted Publishing has not been confirmed and cannot be introspected from the public package index. Do not create/push `v0.1.1` until the existing PyPI project `agent-bootstrap` has a trusted publisher matching GitHub owner `marcelodevops`, repository `agent-bootstrap`, workflow filename `release.yml`, and environment `pypi`. Add it at `https://pypi.org/manage/project/agent-bootstrap/settings/publishing/`, then resume this automation. No production tag or publication has occurred.
