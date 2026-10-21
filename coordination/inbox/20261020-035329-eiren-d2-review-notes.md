# D2 independent review — changes requested

- **Author**: Eiren (Coordinator)
- **Recipient**: agy (assignment owner)
- **Assignment**: [../assignments/bootstrap-d2.md](../assignments/bootstrap-d2.md)
- **Kind**: review feedback
- **Paired worker result**: [../outbox/20261020-035130-agy-d2-result.md](../outbox/20261020-035130-agy-d2-result.md)
- **Independent reviewer**: `/root/review_d1_correction` (read-only)
- **Base revision**: `d43efee11d6c4ce9dce0e815d583690dcac32c3d`

## Finding — P2: `--no-graphify` can still be described as Graphify

`_echo_create_summary()` infers `has_graphify` from any file under `graphify-out/`. However, the composer always creates `<outputs_dir>/.gitkeep`, even with Graphify disabled. Reproduction: `projboot create sample -l python --no-graphify --outputs-dir graphify-out`.

The hook status says Graphify was not selected, but the summary also labels `graphify-out/.gitkeep` as the Graphify placeholder, suggests `graphify update .`, and reports a pending graph. That directory is the selected outputs directory; these Graphify claims are false.

Correct the Graphify summary to distinguish the selected integration from an arbitrary composed path. At minimum, guard Graphify-specific placeholder, command, and pending lines on `not no_graphify` and the actual built-in `graphify-out/.gitkeep` artifact; label the integration itself separately from the configurable outputs directory. Do not remove or rewrite user-selected output files.

Add a focused regression using the real composed plan and `--outputs-dir graphify-out --no-graphify`. Assert output still reports the custom output directory but does not call it a Graphify placeholder, offer `graphify update .`, or report a Graphify graph as pending. Keep existing enabled-Graphify status coverage.

## Verification required

Run the focused D2 file, full suite `/tmp/projboot-execution-venv/bin/python -m pytest -q -c pyproject.toml tests`, and `git diff --check`. Write NEW paired correction result/review-request files with actual commands/results and exact changed files. Do not commit, push, edit `plan.json`/`STATUS.md`, or expand scope. D2 remains unaccepted.

## Other review notes

The independent reviewer found hook outcome parsing conservative: it reports hook success only when the concrete success message exists, and calls `--clone` wiring complete only when both origin and initial-commit success messages exist. No other D2 blocker was found. A failed `add_file()` during live GitHub upload can exit before the summary and leave partial-upload detail; record this as a limitation for E1's external-operation scope rather than broadening this correction.
