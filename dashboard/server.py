"""Read-only local HTTP server for the Agent Bootstrap coordination dashboard.

Uses only the Python standard library. Serves static assets from dashboard/static/
and exposes read-only JSON endpoints for coordination state and allowlisted
evidence/log files.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import errno
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from zoneinfo import ZoneInfo


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
SANTIAGO_TZ = ZoneInfo("America/Santiago")

PROJECT_REL_DIR = "coordination/projects/project-bootstrapper"
PLAN_REL_PATH = f"{PROJECT_REL_DIR}/plan.json"
RUNS_REL_DIR = f"{PROJECT_REL_DIR}/runs"
LOGS_REL_DIR = f"{PROJECT_REL_DIR}/logs"

ALLOWED_DOC_PREFIXES: tuple[str, ...] = (
    "coordination/assignments",
    "coordination/inbox",
    "coordination/outbox",
    LOGS_REL_DIR,
)

REQUIRED_PROJECT_FIELDS: tuple[str, ...] = (
    "project",
    "goal",
    "timezone",
    "created_at",
    "updated_at",
    "workspace",
    "source_repo",
    "coordination_repo",
    "plan_path",
    "coordinator",
    "tasks",
)

REQUIRED_TASK_FIELDS: tuple[str, ...] = (
    "id",
    "title",
    "owner",
    "phase",
    "dependencies",
    "state",
    "assignment",
    "reviewed_at",
    "evidence",
)

REQUIRED_RUN_FIELDS: tuple[str, ...] = (
    "id",
    "task_id",
    "owner",
    "started_at",
    "finished_at",
    "execution_state",
    "exit_code",
    "duration_seconds",
    "log_path",
    "pid",
    "last_event_at",
)

VALID_EXECUTION_STATES: frozenset[str] = frozenset(
    {"running", "finished", "failed", "launch_failed"}
)

PHASE_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    ("A", "Phase A", "Safe & Coherent Generation"),
    ("B", "Phase B", "Working Technical Starters"),
    ("C", "Phase C", "Actionable Agent Context"),
    ("D", "Phase D", "Preview & First Steps"),
    ("E", "Phase E", "GitHub & Reliable Releases"),
    ("Visibility", "Visibility Track", "Local Coordination Dashboard"),
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
ALLOWED_STATIC_FILES: dict[str, tuple[str, str]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/static/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/static/app.js": ("app.js", "application/javascript; charset=utf-8"),
}

MAX_FILE_BYTES = 512 * 1024


def now_santiago() -> datetime:
    return datetime.now(SANTIAGO_TZ)


def format_santiago(dt: datetime) -> str:
    return dt.astimezone(SANTIAGO_TZ).isoformat(timespec="seconds")


def parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(SANTIAGO_TZ)
    except ValueError:
        return None


def check_pid_status(pid: Any) -> tuple[bool, str]:
    """Check whether a local PID exists in the OS process table without mutating state.

    Returns (pid_alive, status_kind) where status_kind is one of:
    'pid_present', 'pid_gone', or 'invalid_pid'.
    """
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False, "invalid_pid"
    try:
        os.kill(pid, 0)
        return True, "pid_present"
    except ProcessLookupError:
        return False, "pid_gone"
    except PermissionError:
        return True, "pid_present"
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False, "pid_gone"
        if exc.errno == errno.EPERM:
            return True, "pid_present"
        return False, "invalid_pid"


def _has_symlink_in_chain(root: Path, target: Path) -> bool:
    """Return True if any path segment from root to target is a symbolic link."""
    try:
        rel = target.relative_to(root)
    except ValueError:
        return True
    current = root
    if current.is_symlink():
        return True
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def resolve_allowlisted_file(repo_root: Path, raw_path: str) -> tuple[int, str, Path | None]:
    """Validate and resolve a repo-relative path against ALLOWED_DOC_PREFIXES.

    Returns (http_status, normalized_rel_path_or_error, resolved_path_or_None).
    """
    if not isinstance(raw_path, str) or not raw_path:
        return HTTPStatus.FORBIDDEN, "Empty file path is not allowed.", None
    if "\x00" in raw_path or "\\" in raw_path or raw_path.startswith("/"):
        return HTTPStatus.FORBIDDEN, "Path must be a clean repo-relative POSIX path.", None

    parts = raw_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return HTTPStatus.FORBIDDEN, "Path traversal segments are not allowed.", None

    norm_rel = "/".join(parts)
    matched_prefix: str | None = None
    for prefix in ALLOWED_DOC_PREFIXES:
        if norm_rel.startswith(prefix + "/") and len(norm_rel) > len(prefix) + 1:
            matched_prefix = prefix
            break

    if matched_prefix is None:
        return (
            HTTPStatus.FORBIDDEN,
            "Path is outside allowlisted directories (assignments, inbox, outbox, project logs).",
            None,
        )

    candidate = repo_root / norm_rel
    if _has_symlink_in_chain(repo_root, candidate):
        return HTTPStatus.FORBIDDEN, "Symbolic links are not permitted.", None

    try:
        root_real = repo_root.resolve(strict=True)
        allowed_dir_real = (repo_root / matched_prefix).resolve(strict=False)
        target_real = candidate.resolve(strict=False)
    except OSError:
        return HTTPStatus.FORBIDDEN, "Unable to resolve path safely.", None

    if not allowed_dir_real.is_relative_to(root_real) or not target_real.is_relative_to(allowed_dir_real):
        return HTTPStatus.FORBIDDEN, "Path escapes allowlisted root.", None

    if not candidate.exists() or not candidate.is_file():
        return HTTPStatus.NOT_FOUND, "Requested file does not exist.", None

    return HTTPStatus.OK, norm_rel, target_real


def _discover_task_messages(repo_root: Path, task_id: str) -> list[dict[str, str]]:
    """Find existing inbox/outbox Markdown files matching a task ID without inventing data."""
    discovered: list[dict[str, str]] = []
    needle = f"-{task_id.lower()}-"
    for kind, folder in (("inbox", "coordination/inbox"), ("outbox", "coordination/outbox")):
        dir_path = repo_root / folder
        if not dir_path.exists() or not dir_path.is_dir() or dir_path.is_symlink():
            continue
        for entry in sorted(dir_path.glob("*.md")):
            if entry.is_symlink() or not entry.is_file():
                continue
            name_lower = entry.name.lower()
            if needle in name_lower:
                discovered.append(
                    {
                        "kind": kind,
                        "name": entry.name,
                        "path": f"{folder}/{entry.name}",
                    }
                )
    return discovered


def build_state_payload(repo_root: Path) -> dict[str, Any]:
    """Read plan.json and runs/*.json from repo_root and return an honest state snapshot."""
    observed_dt = now_santiago()
    observed_at = format_santiago(observed_dt)
    errors: list[dict[str, str]] = []

    plan_path = repo_root / PLAN_REL_PATH
    raw_plan: dict[str, Any] | None = None

    if not plan_path.exists():
        errors.append(
            {
                "path": PLAN_REL_PATH,
                "error": "Missing plan.json file.",
            }
        )
    elif not plan_path.is_file() or _has_symlink_in_chain(repo_root, plan_path):
        errors.append(
            {
                "path": PLAN_REL_PATH,
                "error": "plan.json is not a regular file.",
            }
        )
    else:
        try:
            loaded = json.loads(plan_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                errors.append(
                    {
                        "path": PLAN_REL_PATH,
                        "error": "plan.json root must be a JSON object.",
                    }
                )
            else:
                missing_fields = [f for f in REQUIRED_PROJECT_FIELDS if f not in loaded]
                if missing_fields:
                    errors.append(
                        {
                            "path": PLAN_REL_PATH,
                            "error": f"plan.json missing required fields: {', '.join(missing_fields)}",
                        }
                    )
                elif not isinstance(loaded.get("tasks"), list):
                    errors.append(
                        {
                            "path": PLAN_REL_PATH,
                            "error": "plan.json 'tasks' field must be a list.",
                        }
                    )
                else:
                    raw_plan = loaded
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                {
                    "path": PLAN_REL_PATH,
                    "error": f"Failed to parse plan.json: {exc}",
                }
            )

    # Parse removed_agents and active_team from raw_plan if available
    removed_agents_list: list[dict[str, str]] = []
    removed_agent_names: set[str] = set()
    if raw_plan is not None and "removed_agents" in raw_plan:
        raw_removed = raw_plan.get("removed_agents")
        if not isinstance(raw_removed, list):
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#removed_agents",
                    "error": "'removed_agents' must be a list of objects.",
                }
            )
        else:
            for r_idx, item in enumerate(raw_removed):
                if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip():
                    r_name = item["name"].strip()
                    removed_agent_names.add(r_name)
                    removed_agents_list.append(
                        {
                            "name": r_name,
                            "removed_at": str(item.get("removed_at") or ""),
                            "reason": str(item.get("reason") or ""),
                        }
                    )
                else:
                    errors.append(
                        {
                            "path": f"{PLAN_REL_PATH}#removed_agents[{r_idx}]",
                            "error": "Invalid removed_agent entry.",
                        }
                    )

    active_team_from_plan: list[str] | None = None
    if raw_plan is not None and "active_team" in raw_plan:
        raw_team = raw_plan.get("active_team")
        if not isinstance(raw_team, list) or not all(isinstance(x, str) and x.strip() for x in raw_team):
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#active_team",
                    "error": "'active_team' must be a list of non-empty agent name strings.",
                }
            )
        else:
            active_team_from_plan = [
                x.strip() for x in raw_team if x.strip() not in removed_agent_names
            ]

    # Read runs/*.json without creating directories or inventing run records
    runs_dir = repo_root / RUNS_REL_DIR
    valid_runs: list[dict[str, Any]] = []
    if runs_dir.exists() and runs_dir.is_dir() and not _has_symlink_in_chain(repo_root, runs_dir):
        for run_file in sorted(runs_dir.glob("*.json")):
            rel_run_path = f"{RUNS_REL_DIR}/{run_file.name}"
            if run_file.is_symlink() or not run_file.is_file():
                errors.append(
                    {
                        "path": rel_run_path,
                        "error": "Run record is not a regular file.",
                    }
                )
                continue
            try:
                run_obj = json.loads(run_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(
                    {
                        "path": rel_run_path,
                        "error": f"Malformed run JSON: {exc}",
                    }
                )
                continue

            if not isinstance(run_obj, dict):
                errors.append(
                    {
                        "path": rel_run_path,
                        "error": "Run record root must be a JSON object.",
                    }
                )
                continue

            missing_run_keys = [k for k in REQUIRED_RUN_FIELDS if k not in run_obj]
            if missing_run_keys:
                errors.append(
                    {
                        "path": rel_run_path,
                        "error": f"Run record missing keys: {', '.join(missing_run_keys)}",
                    }
                )
                continue

            exec_state = run_obj.get("execution_state")
            if exec_state not in VALID_EXECUTION_STATES:
                errors.append(
                    {
                        "path": rel_run_path,
                        "error": f"Unknown execution_state: {exec_state!r}",
                    }
                )
                continue

            started_dt = parse_iso_timestamp(run_obj.get("started_at"))
            finished_dt = parse_iso_timestamp(run_obj.get("finished_at"))
            last_event_dt = parse_iso_timestamp(run_obj.get("last_event_at"))

            raw_pid = run_obj.get("pid")
            pid_alive, pid_kind = check_pid_status(raw_pid)
            raw_duration = run_obj.get("duration_seconds")
            if isinstance(raw_duration, bool) or not isinstance(raw_duration, (int, float)):
                raw_duration = None
            else:
                raw_duration = round(float(raw_duration), 3)

            # Determine honest observation_state without mutating historical files
            # or accruing infinite live time when a 'running' PID is gone.
            elapsed_seconds: float | None = None
            if exec_state == "running":
                if pid_alive:
                    observation_state = "pid_present_unverified"
                    observation_label = (
                        f"Reported running · PID {raw_pid} exists locally "
                        "(PID presence does not prove active task work or acceptance)"
                    )
                    if raw_duration is not None:
                        elapsed_seconds = raw_duration
                    elif started_dt is not None:
                        delta = (observed_dt - started_dt).total_seconds()
                        elapsed_seconds = round(max(0.0, delta), 1)
                elif pid_kind == "pid_gone":
                    observation_state = "interrupted"
                    observation_label = (
                        f"Reported running, but PID {raw_pid} is no longer present "
                        "(interrupted / unknown — not verified active)"
                    )
                    elapsed_seconds = raw_duration
                else:
                    observation_state = "unknown"
                    observation_label = (
                        "Reported running, but PID is missing or invalid "
                        "(unknown state — not verified active)"
                    )
                    elapsed_seconds = raw_duration
            elif exec_state == "finished":
                observation_state = "finished"
                observation_label = (
                    f"Process finished (exit {run_obj.get('exit_code')}) · "
                    "Process termination does not equal coordinator acceptance"
                )
                elapsed_seconds = raw_duration
            else:
                observation_state = str(exec_state)
                observation_label = (
                    f"Process {exec_state} (exit {run_obj.get('exit_code')})"
                )
                elapsed_seconds = raw_duration

            log_path = run_obj.get("log_path")
            log_available = False
            if isinstance(log_path, str) and log_path:
                st_code, _, _ = resolve_allowlisted_file(repo_root, log_path)
                log_available = st_code == HTTPStatus.OK

            run_owner = str(run_obj["owner"])
            owner_removed = run_owner in removed_agent_names or (
                active_team_from_plan is not None and run_owner not in active_team_from_plan
            )

            enriched_run = {
                "id": str(run_obj["id"]),
                "task_id": str(run_obj["task_id"]),
                "owner": run_owner,
                "owner_removed": owner_removed,
                "started_at": format_santiago(started_dt) if started_dt else run_obj.get("started_at"),
                "finished_at": format_santiago(finished_dt) if finished_dt else run_obj.get("finished_at"),
                "execution_state": exec_state,
                "observation_state": observation_state,
                "observation_label": observation_label,
                "pid_alive": pid_alive,
                "exit_code": run_obj.get("exit_code"),
                "duration_seconds": raw_duration,
                "elapsed_seconds": elapsed_seconds,
                "log_path": log_path if isinstance(log_path, str) else None,
                "log_available": log_available,
                "pid": raw_pid,
                "last_event_at": format_santiago(last_event_dt) if last_event_dt else run_obj.get("last_event_at"),
                "source_file": rel_run_path,
            }
            valid_runs.append(enriched_run)

    valid_runs.sort(key=lambda r: (str(r.get("started_at") or ""), str(r.get("id") or "")))

    if raw_plan is None:
        return {
            "ok": False,
            "status": "error",
            "observed_at": observed_at,
            "timezone": "America/Santiago",
            "errors": errors,
            "project": None,
            "removed_agents": removed_agents_list,
            "summary": {
                "accepted_count": 0,
                "total_count": 0,
                "by_state": {},
            },
            "phases": [],
            "agents": [],
            "tasks": [],
            "runs": valid_runs,
        }

    # Index runs by task_id
    runs_by_task: dict[str, list[dict[str, Any]]] = {}
    for run in valid_runs:
        runs_by_task.setdefault(run["task_id"], []).append(run)

    # First pass to identify accepted tasks
    raw_tasks = raw_plan.get("tasks", [])
    accepted_task_ids: set[str] = set()
    for t in raw_tasks:
        if isinstance(t, dict) and t.get("state") == "accepted" and isinstance(t.get("id"), str):
            accepted_task_ids.add(t["id"])

    enriched_tasks: list[dict[str, Any]] = []
    by_state_counts: dict[str, int] = {}

    for idx, t in enumerate(raw_tasks):
        if not isinstance(t, dict):
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#tasks[{idx}]",
                    "error": "Task entry is not a JSON object.",
                }
            )
            continue

        missing_task_keys = [k for k in REQUIRED_TASK_FIELDS if k not in t]
        if missing_task_keys:
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#tasks[{idx}]",
                    "error": f"Task missing required fields: {', '.join(missing_task_keys)}",
                }
            )
            continue

        # Validate string fields on task
        bad_str_fields = [
            f for f in ("id", "title", "owner", "phase", "state") if not isinstance(t.get(f), str)
        ]
        if bad_str_fields:
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#tasks[{idx}]",
                    "error": f"Task fields must be strings: {', '.join(bad_str_fields)}",
                }
            )
            continue

        task_id = str(t["id"])
        task_owner = str(t["owner"])
        task_state = str(t["state"])
        by_state_counts[task_state] = by_state_counts.get(task_state, 0) + 1

        # Validate dependencies (must be list of strings)
        raw_deps = t.get("dependencies")
        if not isinstance(raw_deps, list) or not all(isinstance(d, str) for d in raw_deps):
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#tasks[{idx}].dependencies",
                    "error": f"Task {task_id} 'dependencies' must be a list of strings.",
                }
            )
            deps = [str(d) for d in raw_deps if isinstance(d, str)] if isinstance(raw_deps, list) else []
        else:
            deps = [str(d) for d in raw_deps]

        unmet_deps = [d for d in deps if d not in accepted_task_ids]

        all_task_runs = runs_by_task.get(task_id, [])
        active_owner_runs = [
            r for r in all_task_runs if not r["owner_removed"] and r["owner"] == task_owner
        ]
        historical_runs = [
            r for r in all_task_runs if r["owner_removed"] or r["owner"] != task_owner
        ]

        if task_state == "planned":
            latest_run = active_owner_runs[-1] if active_owner_runs else None
        else:
            latest_run = active_owner_runs[-1] if active_owner_runs else (all_task_runs[-1] if all_task_runs else None)

        raw_reviewed_at = t.get("reviewed_at")
        reviewed_at_str: str | None = None
        if raw_reviewed_at is not None:
            if not isinstance(raw_reviewed_at, str):
                errors.append(
                    {
                        "path": f"{PLAN_REL_PATH}#tasks[{idx}].reviewed_at",
                        "error": f"Task {task_id} 'reviewed_at' must be a string or null.",
                    }
                )
            else:
                reviewed_dt = parse_iso_timestamp(raw_reviewed_at)
                reviewed_at_str = format_santiago(reviewed_dt) if reviewed_dt else raw_reviewed_at

        # Parse optional review_history and notes
        raw_review_history = t.get("review_history")
        review_history: list[dict[str, str]] = []
        latest_review_decision: str | None = None
        if raw_review_history is not None:
            if not isinstance(raw_review_history, list):
                errors.append(
                    {
                        "path": f"{PLAN_REL_PATH}#tasks[{idx}].review_history",
                        "error": f"Task {task_id} 'review_history' must be a list.",
                    }
                )
            else:
                for rh in raw_review_history:
                    if isinstance(rh, dict):
                        decision = str(rh.get("decision") or "")
                        if decision:
                            latest_review_decision = decision
                        review_history.append(
                            {
                                "at": str(rh.get("at") or ""),
                                "decision": decision,
                                "reason": str(rh.get("reason") or ""),
                            }
                        )

        task_notes = str(t["notes"]) if isinstance(t.get("notes"), str) else None
        previous_owner = str(t["previous_owner"]) if isinstance(t.get("previous_owner"), str) else None

        # Determine honest display_state and review_status
        if task_state == "accepted":
            display_state = "accepted"
            review_status = "accepted"
            review_label = (
                f"Accepted by coordinator ({reviewed_at_str})"
                if reviewed_at_str
                else "Accepted by coordinator"
            )
        elif task_state == "dispatched":
            display_state = "dispatched"
            if latest_review_decision == "changes_requested":
                review_status = "changes_requested"
                review_label = (
                    f"Reviewed ({reviewed_at_str or '—'}): changes_requested · "
                    "Correction round dispatched (not accepted yet)"
                )
            else:
                review_status = "pending_review"
                if latest_run is None:
                    review_label = "Dispatched · No worker process recorded yet · Coordinator review pending"
                elif latest_run["observation_state"] == "pid_present_unverified":
                    review_label = "Worker process reported running · Coordinator review pending"
                elif latest_run["observation_state"] in ("interrupted", "unknown"):
                    review_label = (
                        f"Run reported running, but PID {latest_run['pid']} is gone "
                        "(interrupted / unknown) · Coordinator review pending"
                    )
                elif latest_run["execution_state"] == "finished":
                    review_label = (
                        f"Process finished (exit {latest_run['exit_code']}) · "
                        "Awaiting Eiren review (not accepted yet)"
                    )
                else:
                    review_label = (
                        f"Process {latest_run['execution_state']} (exit {latest_run['exit_code']}) · "
                        "Coordinator review pending"
                    )
        elif task_state == "planned":
            display_state = "waiting" if unmet_deps else "planned"
            review_status = "not_started"
            review_label = (
                f"Waiting on dependencies ({', '.join(unmet_deps)})"
                if unmet_deps
                else "Planned · Not yet dispatched by coordinator"
            )
        else:
            display_state = task_state
            review_status = "pending_review" if reviewed_at_str is None else "reviewed"
            review_label = f"State: {task_state}"

        raw_assignment = t.get("assignment")
        assignment_path: str | None = None
        if raw_assignment is not None:
            if not isinstance(raw_assignment, str):
                errors.append(
                    {
                        "path": f"{PLAN_REL_PATH}#tasks[{idx}].assignment",
                        "error": f"Task {task_id} 'assignment' must be a string or null.",
                    }
                )
            else:
                assignment_path = raw_assignment

        assignment_available = False
        if assignment_path:
            st_code, _, _ = resolve_allowlisted_file(repo_root, assignment_path)
            assignment_available = st_code == HTTPStatus.OK

        raw_evidence = t.get("evidence")
        evidence_list: list[dict[str, Any]] = []
        if not isinstance(raw_evidence, list) or not all(isinstance(ev, str) for ev in raw_evidence):
            errors.append(
                {
                    "path": f"{PLAN_REL_PATH}#tasks[{idx}].evidence",
                    "error": f"Task {task_id} 'evidence' must be a list of file path strings.",
                }
            )
            ev_iter = [ev for ev in raw_evidence if isinstance(ev, str)] if isinstance(raw_evidence, list) else []
        else:
            ev_iter = raw_evidence

        for ev in ev_iter:
            if ev:
                st_code, _, _ = resolve_allowlisted_file(repo_root, ev)
                evidence_list.append(
                    {
                        "path": ev,
                        "available": st_code == HTTPStatus.OK,
                    }
                )

        discovered_messages = _discover_task_messages(repo_root, task_id)

        enriched_tasks.append(
            {
                "id": task_id,
                "title": str(t["title"]),
                "owner": task_owner,
                "previous_owner": previous_owner,
                "phase": str(t["phase"]),
                "dependencies": deps,
                "unmet_dependencies": unmet_deps,
                "state": task_state,
                "display_state": display_state,
                "review_status": review_status,
                "review_label": review_label,
                "review_history": review_history,
                "notes": task_notes,
                "assignment": assignment_path,
                "assignment_available": assignment_available,
                "reviewed_at": reviewed_at_str,
                "evidence": [ev["path"] for ev in evidence_list],
                "evidence_files": evidence_list,
                "discovered_messages": discovered_messages,
                "runs": all_task_runs,
                "historical_runs": historical_runs,
                "latest_run": latest_run,
            }
        )

    # Build phase flow A -> B -> C -> D -> E + Visibility
    phases_payload: list[dict[str, Any]] = []
    for phase_id, phase_short, phase_desc in PHASE_DEFINITIONS:
        p_tasks = [t for t in enriched_tasks if t["phase"] == phase_id]
        p_accepted = sum(1 for t in p_tasks if t["state"] == "accepted")
        p_dispatched = sum(1 for t in p_tasks if t["state"] == "dispatched")
        phases_payload.append(
            {
                "id": phase_id,
                "label": phase_short,
                "description": phase_desc,
                "accepted_count": p_accepted,
                "dispatched_count": p_dispatched,
                "total_count": len(p_tasks),
                "tasks": [
                    {
                        "id": t["id"],
                        "title": t["title"],
                        "owner": t["owner"],
                        "state": t["state"],
                        "display_state": t["display_state"],
                        "review_status": t["review_status"],
                        "dependencies": t["dependencies"],
                        "unmet_dependencies": t["unmet_dependencies"],
                        "execution_state": (
                            t["latest_run"]["execution_state"] if t["latest_run"] else None
                        ),
                        "observation_state": (
                            t["latest_run"]["observation_state"] if t["latest_run"] else None
                        ),
                    }
                    for t in p_tasks
                ],
            }
        )

    # Derive active actors from active_team when present, otherwise coordinator + current task owners
    coordinator_name = str(raw_plan.get("coordinator") or "Eiren")
    if active_team_from_plan is not None:
        ordered_actors = list(dict.fromkeys(active_team_from_plan))
    else:
        ordered_actors = [coordinator_name]
        for t in enriched_tasks:
            if t["owner"] not in ordered_actors and t["owner"] not in removed_agent_names:
                ordered_actors.append(t["owner"])

    agents_payload: list[dict[str, Any]] = []
    for actor_name in ordered_actors:
        actor_role = "Coordinator" if actor_name == coordinator_name else "Worker"
        owned = [t for t in enriched_tasks if t["owner"] == actor_name]
        dispatched = [t for t in owned if t["state"] == "dispatched"]
        accepted = [t for t in owned if t["state"] == "accepted"]
        planned = [t for t in owned if t["state"] == "planned"]

        actor_runs = [r for r in valid_runs if r["owner"] == actor_name]
        live_runs = [r for r in actor_runs if r["observation_state"] == "pid_present_unverified"]
        latest_actor_run = live_runs[-1] if live_runs else (actor_runs[-1] if actor_runs else None)

        if actor_role == "Coordinator":
            pending_reviews = [t["id"] for t in enriched_tasks if t["state"] == "dispatched"]
            if pending_reviews:
                activity = f"Coordinating plan · Pending review on dispatched: {', '.join(pending_reviews)}"
            else:
                activity = "Coordinating plan · All dispatched tasks reviewed"
            status_badge = "coordinating"
        else:
            if live_runs:
                r = live_runs[-1]
                activity = (
                    f"Reported running {r['task_id']} (PID {r['pid']} present locally, "
                    f"started {r['started_at']})"
                )
                status_badge = "running"
            elif dispatched:
                d_summaries: list[str] = []
                for dt_task in dispatched:
                    lr = dt_task["latest_run"]
                    if lr is None:
                        d_summaries.append(f"{dt_task['id']} (dispatched, no run record)")
                    elif lr["observation_state"] in ("interrupted", "unknown"):
                        d_summaries.append(
                            f"{dt_task['id']} (reported running, PID {lr['pid']} gone / interrupted, review pending)"
                        )
                    else:
                        d_summaries.append(
                            f"{dt_task['id']} (process {lr['execution_state']}, exit {lr['exit_code']}, awaiting review)"
                        )
                activity = " · ".join(d_summaries)
                status_badge = "awaiting_review"
            elif planned:
                next_task = planned[0]
                if next_task["unmet_dependencies"]:
                    activity = (
                        f"Waiting on {', '.join(next_task['unmet_dependencies'])} "
                        f"before {next_task['id']}"
                    )
                else:
                    activity = f"Planned next: {next_task['id']} (awaiting coordinator dispatch)"
                status_badge = "waiting"
            elif len(owned) > 0 and len(accepted) == len(owned):
                activity = f"All assigned tasks accepted ({len(accepted)}/{len(owned)})"
                status_badge = "completed"
            else:
                activity = "No active tasks assigned"
                status_badge = "waiting"

        agents_payload.append(
            {
                "name": actor_name,
                "role": actor_role,
                "status": status_badge,
                "current_activity": activity,
                "owned_task_ids": [t["id"] for t in owned],
                "dispatched_task_ids": [t["id"] for t in dispatched],
                "accepted_task_ids": [t["id"] for t in accepted],
                "planned_task_ids": [t["id"] for t in planned],
                "latest_run": latest_actor_run,
            }
        )

    created_dt = parse_iso_timestamp(raw_plan.get("created_at"))
    updated_dt = parse_iso_timestamp(raw_plan.get("updated_at"))

    project_metadata = {
        "project": str(raw_plan["project"]),
        "goal": str(raw_plan["goal"]),
        "timezone": str(raw_plan["timezone"]),
        "created_at": format_santiago(created_dt) if created_dt else raw_plan.get("created_at"),
        "updated_at": format_santiago(updated_dt) if updated_dt else raw_plan.get("updated_at"),
        "workspace": str(raw_plan["workspace"]),
        "source_repo": str(raw_plan["source_repo"]),
        "coordination_repo": str(raw_plan["coordination_repo"]),
        "plan_path": str(raw_plan["plan_path"]),
        "coordinator": coordinator_name,
        "active_team": ordered_actors,
    }

    overall_status = "degraded" if errors else "ok"
    accepted_total = sum(1 for t in enriched_tasks if t["state"] == "accepted")
    verified_pid_running = sum(
        1 for r in valid_runs if r["observation_state"] == "pid_present_unverified"
    )
    interrupted_runs = sum(
        1 for r in valid_runs if r["observation_state"] in ("interrupted", "unknown")
    )

    return {
        "ok": True,
        "status": overall_status,
        "observed_at": observed_at,
        "timezone": project_metadata["timezone"],
        "errors": errors,
        "project": project_metadata,
        "removed_agents": removed_agents_list,
        "summary": {
            "accepted_count": accepted_total,
            "total_count": len(enriched_tasks),
            "dispatched_count": by_state_counts.get("dispatched", 0),
            "planned_count": by_state_counts.get("planned", 0),
            "running_processes_count": verified_pid_running,
            "interrupted_processes_count": interrupted_runs,
            "by_state": by_state_counts,
        },
        "phases": phases_payload,
        "agents": agents_payload,
        "tasks": enriched_tasks,
        "runs": valid_runs,
    }


class DashboardHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer holding the configured repository root."""

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseHTTPRequestHandler],
        repo_root: Path,
    ) -> None:
        self.repo_root = repo_root.resolve()
        super().__init__(server_address, request_handler_class)


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Read-only HTTP handler for /api/state, /api/file, and static dashboard assets."""

    server: DashboardHTTPServer  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _reject_method(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_security_headers()
        body = b'{"ok": false, "error": "Read-only dashboard: method not allowed."}\n'
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        self._reject_method()

    def do_PUT(self) -> None:
        self._reject_method()

    def do_DELETE(self) -> None:
        self._reject_method()

    def do_PATCH(self) -> None:
        self._reject_method()

    def do_HEAD(self) -> None:
        self._handle_request(send_body=False)

    def do_GET(self) -> None:
        self._handle_request(send_body=True)

    def _handle_request(self, send_body: bool) -> None:
        parsed = urlparse(self.path)
        raw_path = parsed.path
        unquoted_path = unquote(raw_path)

        if "\x00" in raw_path or "\x00" in unquoted_path or "\\" in raw_path or "\\" in unquoted_path:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Invalid path characters."})
            return

        if unquoted_path == "/api/state":
            try:
                payload = build_state_payload(self.server.repo_root)
            except Exception as exc:
                payload = {
                    "ok": False,
                    "status": "error",
                    "observed_at": format_santiago(now_santiago()),
                    "timezone": "America/Santiago",
                    "errors": [
                        {
                            "path": PLAN_REL_PATH,
                            "error": f"Unhandled state inspection error: {exc}",
                        }
                    ],
                    "project": None,
                    "removed_agents": [],
                    "summary": {"accepted_count": 0, "total_count": 0, "by_state": {}},
                    "phases": [],
                    "agents": [],
                    "tasks": [],
                    "runs": [],
                }
            if send_body:
                self._send_json(HTTPStatus.OK, payload)
            else:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self._send_security_headers()
                self.end_headers()
            return

        if unquoted_path in ("/api/file", "/api/doc"):
            query = parse_qs(parsed.query, keep_blank_values=True)
            requested = (query.get("path") or [""])[0]
            status_code, msg_or_rel, resolved = resolve_allowlisted_file(
                self.server.repo_root, requested
            )
            if status_code != HTTPStatus.OK or resolved is None:
                self._send_json(
                    status_code,
                    {
                        "ok": False,
                        "error": msg_or_rel,
                        "requested_path": requested,
                    },
                )
                return

            try:
                raw_bytes = resolved.read_bytes()
                truncated = len(raw_bytes) > MAX_FILE_BYTES
                if truncated:
                    raw_bytes = raw_bytes[:MAX_FILE_BYTES]
                content = raw_bytes.decode("utf-8", errors="replace")
                stat = resolved.stat()
                modified_at = format_santiago(datetime.fromtimestamp(stat.st_mtime, tz=SANTIAGO_TZ))
            except OSError as exc:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": f"Failed to read file: {exc}"},
                )
                return

            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "path": msg_or_rel,
                    "content": content,
                    "truncated": truncated,
                    "size_bytes": stat.st_size,
                    "modified_at": modified_at,
                },
            )
            return

        # Static asset serving with strict containment inside STATIC_DIR
        segments = [seg for seg in unquoted_path.split("/") if seg]
        if any(seg in (".", "..") for seg in segments):
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Static path traversal refused."})
            return

        if unquoted_path not in ALLOWED_STATIC_FILES:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Path not in static allowlist."})
            return

        filename, content_type = ALLOWED_STATIC_FILES[unquoted_path]
        asset_path = STATIC_DIR / filename

        if _has_symlink_in_chain(STATIC_DIR, asset_path):
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Static asset symlink refused."})
            return

        try:
            static_real = STATIC_DIR.resolve(strict=True)
            asset_real = asset_path.resolve(strict=True)
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Static asset missing."})
            return

        if not asset_real.is_relative_to(static_real) or not asset_real.is_file():
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Static containment check failed."})
            return

        data = asset_real.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self._send_security_headers()
        self.end_headers()
        if send_body:
            self.wfile.write(data)


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    repo_root: Path | None = None,
) -> DashboardHTTPServer:
    root = (repo_root or Path(__file__).resolve().parent.parent).resolve()
    return DashboardHTTPServer((host, port), DashboardRequestHandler, repo_root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the read-only local Agent Bootstrap coordination dashboard."
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind address (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Bind port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root directory containing coordination/ (default: repo root)",
    )
    args = parser.parse_args(argv)

    server = create_server(host=args.host, port=args.port, repo_root=args.root)
    actual_host, actual_port = server.server_address[:2]
    print(
        f"Dupond read-only dashboard listening on http://{actual_host}:{actual_port} "
        f"(root: {server.repo_root})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
