# E3 TestPyPI RC2 result

- Author: Eiren
- Assignment: `coordination/assignments/bootstrap-e3.md`
- Recipient: coordinator/reviewer
- Kind: candidate publication and installed-artifact verification result
- Dependencies: accepted source/mainline at `f28735990b9a8ce78ee949f05f7e44ac9bee80ff`; reviewed version PR #13 merged.
- Requested decision: accept RC2 candidate evidence and proceed to the separately reviewed stable-version PR.

## Exact source and workflow evidence

- Version-only commit: `7a522ab39edbb20a3e488a089d7264808cd7de05`, changing `bootstrapper.__version__` to `0.1.1rc2`; independent reviewer confirmed this is the only change and valid PEP 440 prerelease.
- Candidate PR #13 merged after hosted `verify` run `39529846198` passed tests, build, twine, installed-wheel CLI and generated-Python smoke checks. Merge commit: `cc9477fc27782b1a2be0d995418e8f92c02a9ee7`.
- TestPyPI workflow run `39529950814` was dispatched with exact reviewed input SHA `7a522ab39edbb20a3e488a089d7264808cd7de05`; required ancestry validation passed. Both `build` and OIDC `publish` jobs succeeded.
- TestPyPI exact version endpoint returned HTTP 200 with `agent-bootstrap` / `0.1.1rc2`. Wheel: `agent_bootstrap-0.1.1rc2-py3-none-any.whl`, SHA-256 `d1291917df5fbcd2d4f3128f0344ce58015c1986a8144ae832a51ed87614d7c1`. Sdist: `agent_bootstrap-0.1.1rc2.tar.gz`, SHA-256 `c4318af0b385bda40e11cc9aff590e39e33309680c0c830c07b0dafbc0463900`. Downloaded artifacts matched both index hashes.
- Disposable installed-artifact verification: installed runtime dependencies (`typer>=0.9`, `PyGithub>=2.0`) separately via production PyPI; installed the downloaded TestPyPI wheel with `--no-deps`; verified `importlib.metadata.version('agent-bootstrap') == '0.1.1rc2'`, both `agent-bootstrap --help` and `projboot --help`, generated Python project, and generated project suite (`2 passed in 0.01s`). This avoids mixed-index resolution.
- Local source verification on candidate source: `215 passed in 13.75s`; build produced wheel+sdist; `twine check` passed both; same wheel's CLI and generated Python project checks passed (2 tests).

## Remaining gates and limitations

RC2 is the first successful TestPyPI publish and actual install. Stable `0.1.1` has not been prepared or published. Next, create a separate one-line stable-version commit/PR from latest `main`; independently review it, run source/build/twine/installed-wheel checks, and compare candidate/stable artifact contents after normalizing only version metadata. Merge only after hosted verification. Inspect PyPI Trusted Publishing setup before creating/pushing a stable tag; the user confirmed only the TestPyPI publisher setup. Production PyPI currently has only `0.1.0`.
