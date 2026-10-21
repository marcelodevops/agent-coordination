# Bounded reviewer helper

This stdlib-only helper prepares a review packet, validates a structured reviewer
report and evaluates narrowly authorized automatic acceptance. It does not launch
agents, run checks, monitor folders, merge, push or publish anything. The coordinator
explicitly dispatches a read-only subagent using the packet's instructions and
collects its JSON report. Existing dashboard needs no changes: accepted state and
review history use the existing plan fields.

## Trust boundary

**Policy and independent verification are coordinator-owned inputs.** Keep them
outside worker-writable directories and never derive their permissions, category,
identity or check results from a worker/reviewer's prose. This local helper cannot
authenticate agents or enforce OS isolation; the coordinator/orchestrator attests
identities and records independently observed checks. String identities alone are
not a security boundary. Worker, reviewer and verifier must be distinct.

Packets, reports and verification bind to HEAD, full tracked diff, changed file
bytes and all nonignored untracked file bytes. Ignored files are not reviewed or
authorized for acceptance. Assignment and evidence bytes are also bound. Symlink
changes require manual review. Use an isolated reviewed worktree; packets,
reports, policy, verification and plan/receipt should live outside that worktree.
No commands found inside review inputs are executed.
Untracked text-file contents are included in the packet for inspection. Binary or
non-UTF-8 changes are ineligible for autoaccept and require manual coordinator review.

Autoaccept defaults off. Explicit coordinator policy can enable only `docs`,
`tests` or `formatting`; list exact allowed file paths, all required checks and
checklist IDs. Sensitive paths are denied as an additional guard, **not a complete
security classifier**. Coordinator must classify release, auth/security, remote,
destructive and coordination-policy changes for manual review. Zero findings,
all checks passed (no skips), all checklist items passed, accepted dependencies,
matching task owner/state and current snapshot are required.

## Usage

From this repository, prepare a new packet outside the reviewed repository:

```sh
python3 -m reviewer prepare --repo /path/to/worktree --task DOC1 \
  --assignment /path/to/assignment.md --evidence /path/to/worker-result.md \
  --output /path/to/reviews/DOC1-packet.json
```

Give that packet to an explicitly dispatched **read-only reviewer subagent**. It
returns JSON (the findings list must be empty for autoaccept):

```json
{
  "task_id": "DOC1",
  "snapshot": "<packet snapshot>",
  "reviewer": "reviewer-1",
  "recommendation": "accept",
  "findings": [],
  "checklist": {"scope": "pass", "correctness": "pass"}
}
```

A finding uses `path` (repository-relative), positive integer `line`, severity
`P0`–`P3`, `message` and `reproduction`. Recommendations can also be
`changes_requested`; these never authorize acceptance.

Coordinator policy (do not let workers write this file):

```json
{
  "task_id": "DOC1", "worker": "worker-1", "auto_accept": true,
  "category": "docs", "allowed_paths": ["docs/help.md"],
  "required_checks": ["docs-check"], "checklist": ["scope", "correctness"]
}
```

Independent verification recorded by coordinator, after running the required
checks against the same snapshot:

```json
{
  "task_id": "DOC1", "snapshot": "<packet snapshot>",
  "verifier": "Eiren", "checks": {"docs-check": "pass"}
}
```

Evaluate with **no writes**:

```sh
python3 -m reviewer evaluate --repo /path/to/worktree \
  --packet /path/to/reviews/DOC1-packet.json --report /path/to/reviews/DOC1-report.json \
  --policy /path/to/trusted/DOC1-policy.json --verification /path/to/trusted/DOC1-checks.json
```

To authorize acceptance for precisely that task, add:

```sh
--apply-task DOC1 --plan /path/to/coordination/plan.json \
--receipt /path/to/coordination/new-DOC1-decision.json
```

The plan and receipt must be in the same coordinator Git repository, outside the
reviewed repository. The helper records the receipt with a repository-relative
path, appends review history/evidence and atomically replaces the plan; it never
changes STATUS.md or assignments. A lock protects
against another invocation of this helper. Other plan writers must honor the
sibling `plan.json.review.lock`; do not update a plan concurrently. It also checks
plan bytes before replacement. Receipt is created first with `prepared` status,
then marked `applied`: after interruption, inspect the plan review history to
resolve an unfinished receipt. No rollback of accepted task happens implicitly.
Filesystem permissions and coordinator-controlled inputs remain essential.

Exit codes: 0 success/eligible, 1 not eligible, 2 invalid input/application error.
No live tasks are autoaccepted by installation or tests.

## Tests

```sh
python3 -m unittest discover -s reviewer/tests -v
```
