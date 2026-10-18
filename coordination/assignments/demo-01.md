# demo-01: verify the basic handoff contract

Author: coordinator
Assigned to: demo-worker
Recipient: coordinator
Kind: assignment
Dependencies: existing repository documentation only; no other worker tasks
State: accepted by coordinator on 2026-10-09

## Objective

Produce one short, evidence-backed description of how an assignment reaches a worker and how its result reaches coordinator review.

## Inputs

Read AGENTS.md, STARTING-POINT.md, coordination/RULES.md, coordination/STATUS.md, this assignment, and the README.md files in coordination/assignments, inbox and outbox.

## Ownership

You may create exactly one new result Markdown file in coordination/outbox and one new review-request Markdown file in coordination/inbox. Follow the naming rule. Do not edit any existing file. You are not alone in the repository: preserve all other edits, including the untracked .gitignore. Only the coordinator updates assignments and status.

## Required output

The outbox result must identify author, assignment, recipient, kind, dependencies and requested result/decision. Include input paths, a concise assignment -> dispatch -> result -> review sequence, changed files, evidence tied to specific rule numbers, and limitations. State explicitly that repository files alone do not dispatch or monitor agents; this demonstration uses an explicit tool dispatch and coordinator inspection.

The inbox message must request coordinator review and link to the outbox result using a relative Markdown link. No invented blocker or user decision is needed.

## Acceptance criteria

1. Both new messages exist with required metadata and valid relative links.
2. The result accurately describes ownership and completion under rules 1, 6 and 8.
3. Inputs, changed files and evidence are recorded, and conventions are distinguished from automation.
4. No existing file is changed by the worker; no product code, dependencies or framework is added.

## Dispatch

Coordinator explicitly invokes one subagent and provides this assignment path. The worker reads the files directly; the user relays no messages. The coordinator reads both outputs and records acceptance or required corrections in STATUS.md.

## Coordinator decision

Accepted. Both messages satisfy the four acceptance criteria. Review and evidence are recorded in [STATUS.md](../STATUS.md).
