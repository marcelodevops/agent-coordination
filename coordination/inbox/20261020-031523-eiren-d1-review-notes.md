# D1 independent review — changes requested

- **Author**: Eiren (Coordinator)
- **Recipient**: Mr.Q (owner)
- **Assignment**: [../assignments/bootstrap-d1.md](../assignments/bootstrap-d1.md)
- **Kind**: `review-feedback`
- **Paired worker result**: [../outbox/20261020-030854-mrq-d1-result.md](../outbox/20261020-030854-mrq-d1-result.md)
- **Independent reviewer**: `/root/review_d1`
- **Base revision**: `6a9e5249646a2becfdc1290728f81fd3ae8549ea`

## Finding — P2: target-state race can bypass refusal

In `bootstrapper/cli.py`, `_validate_write_plan()` checks whether the target is nonempty and returns only the plan. `_write_local()` then calls `_is_nonempty_dir()` again and uses that second observation to choose merge versus staging. If a target that was absent/empty during preflight becomes nonempty before the second check, `create` without `--force` can enter the forced-merge path and overwrite a planned file. Before D1, one `nonempty_existing` snapshot controlled both refusal and write-path selection; if the target appeared after that snapshot, staging/replace failed rather than merging into it.

Keep the refusal and write-path decision tied to one preflight snapshot, or revalidate the no-force refusal before any write. Add a focused regression that deterministically simulates the target appearing after preflight and proves no existing file is overwritten. Preserve existing forced-merge behavior and preview's read-only behavior.

Evidence: reviewer identified the split observation at `bootstrapper/cli.py` lines 236–263; prior behavior at base revision `6a9e524` lines 221–243. Coordinator independently ran focused preview tests (18 passed) and full suite (190 passed in 10.99s); `git diff --check` was clean. The issue is a safety-path gap not covered by those passing tests.

## Other review points

The shared composition path, preview action labeling, zero-write structure and path-parity assertions look sound. A forced-merge preview parity case is a useful optional test, but is not required for this correction unless it naturally fits the focused test change.

## Required correction handoff

Address the race and add the deterministic regression. Run the focused preview tests, full suite `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`, and `git diff --check`. Write a NEW paired result/review-request handoff with actual command output and exact changed files/revision. Do not commit, push, publish, or change plan/STATUS; Eiren owns acceptance.
