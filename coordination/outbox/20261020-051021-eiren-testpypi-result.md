# Eiren result — TestPyPI candidate gate

- Assignment: E3 plus delegated candidate verification
- Intended recipient: coordinator record / user
- Kind: result and external blocker
- Exact merged product source: `93fa7c50a38bfe7faadf8778ecd98831b4b28d4f` (PR #9 merge); candidate version commit `4d807f439ef9c4c7a6b2778ee878be3214d91a22` changes only `bootstrapper/__init__.py` from `0.1.0` to `0.1.1rc1`.
- PR #7 merged at `93b3a82111472e6d3525da4aea10d02dd4150894`; hosted CI `verify` passed. PR #9 merged at `93fa7c50a38bfe7faadf8778ecd98831b4b28d4f`; hosted CI `verify` passed. Read-only independent review confirmed the one-line version change is PEP 440-valid and dynamic package metadata uses it.
- Candidate workflow run: https://github.com/marcelodevops/agent-bootstrap/actions/runs/39391239668. Exact merged-main ancestry gate, source suite, build, twine validation, installed wheel CLI smoke, generated Python project tests, and artifact upload all passed. TestPyPI publish failed with `invalid-publisher`: valid OIDC token but no matching publisher configuration. The displayed expected claims were repository `marcelodevops/agent-bootstrap`, workflow `.github/workflows/testpypi.yml`, environment `testpypi`.
- Confirmed `https://test.pypi.org/pypi/agent-bootstrap/0.1.1rc1/json` returns HTTP 404; no candidate upload occurred.
- A previous accidental dispatch against stable `0.1.0` (run 39390879825) completed the build job checks, then its publish job was cancelled before execution. It did not publish.
- Local candidate source suite: 218 passed in 19.62s. Candidate build and twine checks passed. Installed wheel exposed both CLI commands; generated Python starter installed and tests passed (2 passed). Candidate artifact SHA-256: wheel `68c34f067a50792abaef9b8fb5f0b0769dbbc4d771c92313b1cace213a349315`; sdist `e8a611df1309f7dd9998b0ee014c04a3a14077d4deea123006c89c71268f91e3`.
- Compared normalized local candidate wheel/sdist against builds from stable source `93b3a82111472e6d3525da4aea10d02dd4150894`: all 14 wheel payload entries and 41 sdist files match after normalizing version metadata; no other artifact differences.
- Remaining gate: TestPyPI account owner must register Trusted Publisher for repository `marcelodevops/agent-bootstrap`, workflow `.github/workflows/testpypi.yml`, environment `testpypi`. Do not proceed with stable release until candidate upload and exact installed TestPyPI verification pass.
- Existing workspace state preserved; product checkout currently reports untracked `uv.lock`. No credentials were read or changed.
