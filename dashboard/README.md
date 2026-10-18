# Agent Coordination — Read-Only Local Dashboard

A small, buildless, standard-library local web dashboard for observing the **Agent Bootstrap** multi-agent coordination loop in this repository.

This dashboard is **strictly read-only**: it never dispatches workers, modifies assignments, creates directories, or marks tasks accepted. Coordinator review and acceptance remain owned by **Eiren** in `coordination/projects/project-bootstrapper/plan.json` and `coordination/STATUS.md`.

---

## Startup Command

Run from your checkout root using Python 3.10 or later (standard library only):

```bash
python3 -m dashboard
```

Or invoke `dashboard/server.py` directly with optional flags:

```bash
python3 dashboard/server.py --host 127.0.0.1 --port 8787
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Loopback interface to bind |
| `--port` | `8787` | TCP port to bind (`0` binds an ephemeral port for testing) |
| `--root` | Repository root | Path to the `agent-coordination` checkout or a test fixture root |

Open `http://127.0.0.1:8787` in a browser once started.

---

## Data Contract

The server reads coordination files relative to `--root`:

1. **Plan & Task State (`coordination/projects/project-bootstrapper/plan.json`)**:
   - **Project fields**: `project`, `goal`, `timezone`, `created_at`, `updated_at`, `workspace`, `source_repo`, `coordination_repo`, `plan_path`, `coordinator`, `tasks`, plus optional `active_team` and `removed_agents`.
   - **Task fields**: `id`, `title`, `owner`, `phase`, `dependencies`, `state`, `assignment`, `reviewed_at`, `evidence`, plus optional `previous_owner`, `review_history`, and `notes`.
   - **Active Actors vs. Removed Agents**: Actor cards (`agents`) are derived from `active_team` when present in `plan.json` (or `coordinator` + current task owners minus `removed_agents` otherwise). Removed agents (such as `Copilot`) never appear as active actors or as `0/0` completed; their historical runs remain preserved in `runs` and task run history with `owner_removed: true`.
   - `task.state` (`planned`, `dispatched`, `accepted`) and `task.reviewed_at` (ISO 8601 in `America/Santiago`) are coordinator-owned and independent of worker CLI process execution.

2. **Worker CLI Run Records (`coordination/projects/project-bootstrapper/runs/*.json`)**:
   - **Run fields**: `id`, `task_id`, `owner`, `started_at`, `finished_at`, `execution_state` (`running` | `finished` | `failed` | `launch_failed`), `exit_code`, `duration_seconds`, `log_path`, `pid`, `last_event_at`.
   - **Process Observation State (`observation_state`)**:
     - Preserves the original `execution_state` as the worker runner report without editing historical JSON files on disk.
     - For runs marked `execution_state: "running"`, checks whether `pid` exists in the local OS process table (`os.kill(pid, 0)`):
       - If the PID is gone (`ESRCH`), sets `observation_state: "interrupted"`, `pid_alive: false`, and `elapsed_seconds: null` so disappeared processes never accrue live runtime forever.
       - If the PID is invalid/missing, sets `observation_state: "unknown"`, `pid_alive: false`, and `elapsed_seconds: null`.
       - If the PID exists locally, sets `observation_state: "pid_present_unverified"`, `pid_alive: true`, and labels clearly that local PID presence does not prove active task work or coordinator acceptance.
   - Timestamps are normalized to ISO 8601 in `America/Santiago`.
   - Unstarted tasks (`state: "planned"` with no active-owner run records) are labeled `planned` / `waiting` with no synthetic dates or fake activity.
   - Summary metrics report exact `accepted_count` and `total_count` without invented percentage estimates.

3. **HTTP Endpoints**:
   - `GET /api/state`: Returns `ok`, `status` (`ok` | `degraded` | `error`), `observed_at` (`America/Santiago` server observation timestamp), `errors` (list of missing or malformed file/field diagnostics), `project`, `removed_agents`, `summary`, `phases` (`A` → `B` → `C` → `D` → `E` + `Visibility`), `agents`, `tasks`, and `runs`.
   - `GET /api/file?path=<repo-relative-path>`: Returns UTF-8 text content and metadata for allowlisted files only.

---

## How State Updates

- **Browser Polling**: The client polls `GET /api/state` every **3 seconds** and displays both the server's `observed_at` timestamp (`America/Santiago`) and the browser's last refresh time.
- **Honest Failure & Unknown Handling**:
  - If `plan.json` is missing or malformed, or if the server cannot be reached, the UI transitions immediately to `✖ ERROR · STATE UNKNOWN` and renders an explicit error alert. Unknown or failed state is never shown as idle or success.
  - If one or more `runs/*.json` files or task fields (e.g., a malformed `dependencies` or `evidence` field) are invalid while `plan.json` is otherwise readable, `/api/state` returns `status: "degraded"`, preserves valid data, and lists every validation error in the warning banner without throwing an unhandled server exception.
- **Process State vs. Review Acceptance**:
  - When a worker CLI process exits with code `0` (`execution_state: "finished"`), the dashboard displays `PROCESS EXITED (0) · NOT ACCEPTED YET` (or `CHANGES REQUESTED` if coordinator review requested fixes) until the coordinator (`Eiren`) updates `task.state` to `"accepted"`.

---

## Security & Containment

- **Loopback Binding**: Binds to `127.0.0.1` by default.
- **Read-Only HTTP Methods**: Only `GET` and `HEAD` are permitted. `POST`, `PUT`, `DELETE`, and `PATCH` return `405 Method Not Allowed`. The UI contains no start, dispatch, or accept buttons.
- **Strict File Viewer Allowlist**: `GET /api/file` only serves regular files inside:
  - `coordination/assignments/`
  - `coordination/inbox/`
  - `coordination/outbox/`
  - `coordination/projects/project-bootstrapper/logs/`
  Any request outside these four prefixes (such as `coordination/STATUS.md`, `plan.json`, `README.md`), any path traversal segment (`..`, `.`, backslashes, URL-encoded `%2e%2e`, NUL bytes, absolute paths), or any symbolic link along the path chain is refused with `403 Forbidden`.
- **Static Asset Containment**: Static routes serve only the allowlisted files inside `dashboard/static/` (`index.html`, `styles.css`, `app.js`) with `Content-Security-Policy: default-src 'self'` and `X-Content-Type-Options: nosniff`.
- **HTML Injection Prevention**: All task fields, error diagnostics, document text, and log contents are rendered in the browser exclusively via DOM `textContent`.

---

## Runtime Limitations

- **Polling Latency**: State updates are polled every 3 seconds rather than pushed over WebSockets or Server-Sent Events.
- **Unverified PID Identity**: `os.kill(pid, 0)` checks whether a numeric PID exists on the local host to detect disappeared worker processes (`observation_state: "interrupted"`), but cannot cryptographically prove that a surviving or recycled PID is making progress on the task (`observation_state: "pid_present_unverified"`).
- **Log Truncation**: Very large log or evidence files (> 512 KB) are truncated to 512 KB in `/api/file` responses with `"truncated": true`.
- **No Native Browser Automation in Unit Tests**: Automated verification in `dashboard/tests/test_dashboard.py` exercises the live HTTP server, JSON payloads, static asset headers, and path/symlink traversal defenses over loopback sockets against isolated temporary fixture roots using Python's `unittest` and `urllib.request`, not a headless browser engine.

---

## Running Tests

```bash
python3 -m unittest discover -s dashboard/tests -t . -v
```

## Shared records and local artifacts

Assignments, inbox/outbox evidence and coordinator decisions are versioned. Worker `runs/` and `logs/` are local and ignored; a fresh clone displays the committed plan and evidence but has no execution history until workers run there. The launcher assignments currently refer to the original local workspaces; review their paths before dispatching on another machine.

The optional `flow.html` and `flow.visual-check*` files are generated local diagram previews; `flow.json` is their versioned source. Python caches, Graphify output and private agent overrides are also ignored. Environment example, sample and template files remain shareable.
