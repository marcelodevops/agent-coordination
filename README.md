# AIMonk

**Coordinate AI agents. Follow the work. Review the evidence.**

AIMonk is a shared workspace and local dashboard for coordinating agent work. Keep assignments, dependencies, worker deliveries and review decisions together so you can see who is doing what without carrying prompts between agents.

The current implementation combines a file-based handoff method, an explicit worker launcher and a read-only browser dashboard. This repository's working example coordinates [agent-bootstrap](https://github.com/marcelodevops/agent-bootstrap); AIMonk is the coordination workspace, while agent-bootstrap creates starter projects.

## See the work

![AIMonk dashboard showing accepted tasks, active agent ownership and roadmap dependencies](resources/Screenshot%202026-10-19%20at%204.56.57%E2%80%AFPM.png)

*Team ownership and the dependency flow at a glance. These are historical screenshots from the agent-bootstrap project, captured before the AIMonk rename; counts, paths and assignments reflect that session.*

![Task table and detail panel separating coordinator acceptance from worker process completion](resources/Screenshot%202026-10-19%20at%204.45.39%E2%80%AFPM.png)

*Inspect a task's owner, dependencies, execution timing, review state and linked evidence. A successful process exit is kept separate from acceptance.*

![Task review showing assignment links, inbox and outbox evidence, execution logs and a plain-text evidence viewer](resources/Screenshot%202026-10-19%20at%203.38.34%E2%80%AFPM.png)

*Follow the handoff through its source files and read the supporting evidence in the same interface.*

## Run locally

You need **Python 3.10 or later**, Git and a browser. The dashboard uses the Python standard library: no package installation, frontend build or API key is needed to view it.

```sh
git clone https://github.com/marcelodevops/aimonk.git
cd aimonk
python3 -m dashboard --port 8787
```

Open [http://127.0.0.1:8787/](http://127.0.0.1:8787/). From an existing checkout, run the last command in its current directory; renaming the repository does not require moving your local workspace.

The browser polls the local API **every three seconds**. Updates come from files written by the worker launcher and coordinator; they are not pushed over an event stream. The dashboard shows refresh times and reports unavailable or malformed state.

A fresh clone includes the committed plan and evidence. Execution records and logs stay local, so historical runtime data shown in these screenshots will not appear in a new clone. The bundled launcher is specific to the current project and local CLI paths; review its workspace, assignments and agent configuration before dispatching on another machine. Viewing the dashboard does not start any workers.

See the [dashboard guide](dashboard/README.md) for the data contract, API, file-viewer boundaries and runtime limitations.

## How coordination works

```text
Bounded assignment → explicit dispatch → worker delivery → review
                                                       ├─ corrections → new delivery
                                                       └─ acceptance → next eligible task
```

1. **Assign:** the coordinator defines the objective, inputs, owned files, dependencies and acceptance criteria.
2. **Dispatch:** the coordinator explicitly launches the authorized worker. Files alone do not wake agents.
3. **Deliver:** the worker writes a new result with changed files, checks and limitations to `outbox/`, plus a review request or blocker to `inbox/`.
4. **Review:** the coordinator checks the delivery and evidence, records acceptance or requested corrections, and dispatches the next eligible assignment.

The dashboard exposes active owners, phase dependencies, task filters, execution start/end times, measured durations, review history and an allowlisted evidence/log viewer. It is read-only: it does not dispatch, edit tasks, accept deliveries or run an unattended coordinator loop.

Start with [STARTING-POINT.md](STARTING-POINT.md), [coordination/RULES.md](coordination/RULES.md) and [coordination/STATUS.md](coordination/STATUS.md). The status file preserves dated decisions; its introductory sections also contain historical setup notes.

## Where things live

| Path | Purpose |
|---|---|
| [coordination/assignments/](coordination/assignments/) | Bounded worker assignments and acceptance criteria |
| [coordination/inbox/](coordination/inbox/) | Questions, blockers and review requests |
| [coordination/outbox/](coordination/outbox/) | Deliveries, verification evidence and limitations |
| [coordination/STATUS.md](coordination/STATUS.md) | Coordinator decisions and handoff disposition |
| [Project plan](coordination/projects/project-bootstrapper/plan.json) | Dashboard task ownership, dependencies and acceptance state |
| [Worker launcher](coordination/projects/project-bootstrapper/run_worker.py) | Explicit CLI dispatch and local execution recording |
| [dashboard/](dashboard/README.md) | Standard-library server and browser interface |

The project folder retains its original `project-bootstrapper` name to preserve existing references. Runtime `runs/`, `logs/`, caches and generated previews are ignored by Git; assignment and evidence files are versioned.

## Development and contributions

Run the dashboard checks from the checkout root:

```sh
python3 -m unittest discover -s dashboard/tests -t . -v
```

`main` is the default integration branch. Start focused work from current `main` on `feat/<topic>`, `fix/<topic>` or `chore/<topic>`. Keep commits separated by task and repository. Push the topic branch, open a pull request targeting `main`, record relevant checks and review the changes before merging. Preserve individual commits with a merge commit when integrating a multi-commit task. Do not push implementation changes directly to `main`.
