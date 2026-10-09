# Starting point

New priority established by the user on 2026-10-09: a separate repository and chat for basic agent coordination. Naviera implementation is not the task here.

## User's motivating request — preserved verbatim

> i am tired of copying and pasting prompts, we should get more basics and define output and input folders for communication or something, we are involuting

## Proposal accepted as the basic starting point — preserved verbatim

Yes. We need a basic shared workspace so you stop carrying messages between agents.

```text
coordination/
  RULES.md              # One agreed approach, binding on every agent
  assignments/
    track-1.md
    track-2.md
    track-3.md
  inbox/                # Questions, blockers and handoff requests
  outbox/               # Results, evidence and completed handoffs
  STATUS.md             # Coordinator-maintained overall state
```

Each agent reads its assignment and the same rules, then writes its results and blockers to those folders. **One coordinator reads them, resolves dependencies and updates the assignments.** You review outcomes and decisions.

The folders need that coordinator loop; otherwise they just become another place where messages accumulate.

We should establish this handoff mechanism before adding more plans or starting parallel implementation.

## User's instruction to establish this project — preserved verbatim

> . This is the new priority. new repo and everything to document, new chat and keep this last prompt as the basic starting point
