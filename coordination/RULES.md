# Coordination rules

1. One coordinator owns this file, assignments and STATUS.md. Workers propose changes in inbox; they do not redefine the approach.
2. Every assignment specifies objective, inputs, owned files, required output and acceptance criteria. No assignment means no worker implementation.
3. Workers read these rules and their current assignment before starting. They preserve other workers' changes and stay inside their ownership.
4. Questions/blockers go in inbox as new Markdown files; results/evidence go in outbox as new Markdown files. Name files YYYYMMDD-HHMMSS-agent-topic.md; add a suffix if a name already exists. Never overwrite another message.
5. Every message identifies author, assignment, intended recipient, kind, dependencies and requested decision or result. Results include changed files, verification evidence and remaining limitations.
6. The coordinator reads pending messages, records decisions and message paths in STATUS.md, updates assignments, and dispatches authorized follow-up through available tools. Files alone do not wake an agent.
7. Keep messages in place. STATUS.md records pending/resolved/reviewed disposition so evidence remains available.
8. Completion requires coordinator review against assignment acceptance criteria. Worker-reported completion alone is not acceptance.
9. Escalate to the user only for a genuine user decision; the coordinator handles routine dependency and handoff questions.
10. First prove one small handoff cycle. Add automation only after that cycle works and its input/output contract is agreed.
