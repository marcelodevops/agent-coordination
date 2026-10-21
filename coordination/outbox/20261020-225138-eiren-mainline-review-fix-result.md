# E3 mainline review and release correction

- Author: Eiren
- Assignment: `coordination/assignments/bootstrap-e3.md`
- Recipient: coordinator/reviewer
- Kind: integrated review result
- Dependencies: E2 accepted; user confirmed TestPyPI Trusted Publisher configured.
- Requested decision: accept the corrected current mainline as the next candidate source; continue with a unique RC2.

## Evidence

- Latest-main check found PR #11 merged at `90c3e97d995a04b96892432944eea4bdd2cc8daf` with hosted CI `verify` successful. An independent read-only review found two concrete issues: derived Helm chart names could exceed 63 characters, and `--from-tree` silently discarded exact collisions with generated paths.
- Added focused fixes and regression tests in commit `ccc7491f3c2fa92c23a3820aa895c8184501b3ed`, PR #12. Independent read-only review found both findings addressed and no regressions in the changed files.
- On exact PR #12 source: full suite `215 passed in 13.78s`; after final formatting, both focused regressions passed (`2 passed in 0.11s`); `git diff --check` passed.
- GitHub hosted run `39529613604` (`verify`) passed source tests, wheel/sdist build, `twine check`, installed-wheel CLI smoke and generated Python project tests.
- PR #12 merged after those gates; merge commit / current main is `f28735990b9a8ce78ee949f05f7e44ac9bee80ff`.
- Production PyPI currently exposes only `0.1.0`; TestPyPI project endpoint remains 404 until first successful publish. Exact candidate `0.1.1rc2` was checked and is absent (404). The previous `0.1.1rc1` upload failed before publication and is also absent.

## Remaining gates and limitations

Create and independently review a version-only RC2 PR from exact main `f28735990b9a8ce78ee949f05f7e44ac9bee80ff`; merge only after required CI. Then dispatch the reviewed TestPyPI workflow at that exact merged SHA. The user has confirmed the pending Trusted Publisher was added, but this configuration is not yet proven until OIDC publication succeeds. Verify the exact RC2 from TestPyPI in a disposable environment before preparing stable `0.1.1`. No candidate or production release has been published in this run.
