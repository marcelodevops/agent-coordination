"""Stdlib unittest coverage for the read-only coordination dashboard.

All tests execute against isolated temporary fixture roots (never real live records).
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dashboard.server import STATIC_DIR, create_server


SAMPLE_PLAN = {
    "project": "Agent Bootstrap",
    "goal": "Crear proyectos listos para desarrollo asistido con agentes",
    "timezone": "America/Santiago",
    "created_at": "2026-10-17T23:24:55-03:00",
    "updated_at": "2026-10-17T23:36:05-03:00",
    "workspace": "/Users/mac/ops/worktrees/project-bootstrapper-plan",
    "source_repo": "/Users/mac/ops/repos/project_bootstrapper",
    "coordination_repo": "/Users/mac/ops/repos/agent-coordination",
    "plan_path": "/Users/mac/ops/worktrees/project-bootstrapper-plan/docs/superpowers/plans/2026-10-17-bootstrap-product-improvement-plan.md",
    "coordinator": "Eiren",
    "active_team": ["Eiren", "Mr.Q", "agy"],
    "removed_agents": [
        {
            "name": "Copilot",
            "removed_at": "2026-10-17T23:28:54-03:00",
            "reason": "User explicitly removed Copilot from the plan; historical runs retained.",
        }
    ],
    "tasks": [
        {
            "id": "A1",
            "title": "Colisiones de rutas y conflictos archivo/directorio",
            "owner": "Mr.Q",
            "phase": "A",
            "dependencies": [],
            "state": "dispatched",
            "assignment": "coordination/assignments/bootstrap-a1.md",
            "reviewed_at": "2026-10-17T23:36:05-03:00",
            "evidence": ["coordination/outbox/20261017-233000-mrq-a1-result.md"],
            "review_history": [
                {
                    "at": "2026-10-17T23:36:05-03:00",
                    "decision": "changes_requested",
                    "reason": "Canonical write preflight still allows internal .. and in-root symlink aliases.",
                }
            ],
            "notes": "Correction round dispatched to Mr.Q; no acceptance yet.",
        },
        {
            "id": "B1",
            "title": "Chart Helm que pasa lint y render",
            "owner": "Mr.Q",
            "previous_owner": "Copilot",
            "phase": "B",
            "dependencies": ["A1"],
            "state": "planned",
            "assignment": None,
            "reviewed_at": None,
            "evidence": [],
            "notes": "Copilot removed by user; reassigned to Mr.Q after A1.",
        },
        {
            "id": "C1",
            "title": "Formatos válidos de adaptadores de agentes",
            "owner": "agy",
            "phase": "C",
            "dependencies": ["V1"],
            "state": "planned",
            "assignment": None,
            "reviewed_at": None,
            "evidence": [],
        },
        {
            "id": "D1",
            "title": "Plan de generación y vista previa sin efectos",
            "owner": "Mr.Q",
            "phase": "D",
            "dependencies": ["A1"],
            "state": "planned",
            "assignment": None,
            "reviewed_at": None,
            "evidence": [],
        },
        {
            "id": "E3",
            "title": "Revisión integrada y evidencia de la versión",
            "owner": "Eiren",
            "phase": "E",
            "dependencies": ["D1"],
            "state": "accepted",
            "assignment": "coordination/assignments/bootstrap-e3.md",
            "reviewed_at": "2026-10-17T23:40:00-03:00",
            "evidence": [],
        },
        {
            "id": "V1",
            "title": "Dashboard local de seguimiento en agent-coordination",
            "owner": "agy",
            "phase": "Visibility",
            "dependencies": [],
            "state": "dispatched",
            "assignment": "coordination/assignments/bootstrap-v1.md",
            "reviewed_at": None,
            "evidence": [],
        },
    ],
}


class DashboardServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self._populate_fixture(self.root)
        self.server = create_server(host="127.0.0.1", port=0, repo_root=self.root)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def _populate_fixture(self, root: Path) -> None:
        proj_dir = root / "coordination" / "projects" / "project-bootstrapper"
        runs_dir = proj_dir / "runs"
        logs_dir = proj_dir / "logs"
        assign_dir = root / "coordination" / "assignments"
        inbox_dir = root / "coordination" / "inbox"
        outbox_dir = root / "coordination" / "outbox"

        for d in (proj_dir, runs_dir, logs_dir, assign_dir, inbox_dir, outbox_dir):
            d.mkdir(parents=True, exist_ok=True)

        (proj_dir / "plan.json").write_text(json.dumps(SAMPLE_PLAN, indent=2), encoding="utf-8")
        (root / "coordination" / "STATUS.md").write_text("# Private status not in file viewer allowlist\n", encoding="utf-8")
        (root / "README.md").write_text("# Top-level README\n", encoding="utf-8")

        (assign_dir / "bootstrap-a1.md").write_text("# Assignment A1\nCheck <script>alert(1)</script>\n", encoding="utf-8")
        (inbox_dir / "20261017-233000-mrq-a1-review.md").write_text("# Review A1\nPlease review.\n", encoding="utf-8")
        (outbox_dir / "20261017-233000-mrq-a1-result.md").write_text("# Result A1\nCompleted tests.\n", encoding="utf-8")
        (logs_dir / "20261017-232520-a1.log").write_text("Running pytest...\n1 passed\n", encoding="utf-8")

        run_a1 = {
            "id": "20261017-232520-a1",
            "task_id": "A1",
            "owner": "Mr.Q",
            "started_at": "2026-10-17T23:25:20-03:00",
            "finished_at": "2026-10-17T23:28:20-03:00",
            "execution_state": "finished",
            "exit_code": 0,
            "duration_seconds": 180.0,
            "log_path": "coordination/projects/project-bootstrapper/logs/20261017-232520-a1.log",
            "pid": 12345,
            "last_event_at": "2026-10-17T23:28:20-03:00",
        }
        (runs_dir / "20261017-232520-a1.json").write_text(json.dumps(run_a1, indent=2), encoding="utf-8")

        # Historical Copilot run on B1 with nonexistent PID
        run_b1_copilot = {
            "id": "20261017-232612-b1",
            "task_id": "B1",
            "owner": "Copilot",
            "started_at": "2026-10-17T23:26:12-03:00",
            "finished_at": None,
            "execution_state": "running",
            "exit_code": None,
            "duration_seconds": None,
            "log_path": "coordination/projects/project-bootstrapper/logs/20261017-232612-b1.log",
            "pid": 99999999,
            "last_event_at": "2026-10-17T23:26:12-03:00",
        }
        (runs_dir / "20261017-232612-b1.json").write_text(json.dumps(run_b1_copilot, indent=2), encoding="utf-8")

        # Active agy run on V1 using current test process PID so PID exists locally
        run_v1 = {
            "id": "20261017-232523-v1",
            "task_id": "V1",
            "owner": "agy",
            "started_at": "2026-10-17T23:25:23-03:00",
            "finished_at": None,
            "execution_state": "running",
            "exit_code": None,
            "duration_seconds": None,
            "log_path": "coordination/projects/project-bootstrapper/logs/20261017-232523-v1.log",
            "pid": os.getpid(),
            "last_event_at": "2026-10-17T23:25:23-03:00",
        }
        (runs_dir / "20261017-232523-v1.json").write_text(json.dumps(run_v1, indent=2), encoding="utf-8")

    def _get(self, path: str) -> tuple[int, dict[str, str], bytes]:
        url = f"http://127.0.0.1:{self.port}{path}"
        try:
            with urlopen(url, timeout=5) as resp:
                return resp.status, dict(resp.headers.items()), resp.read()
        except HTTPError as err:
            return err.code, dict(err.headers.items()), err.read()

    def test_removed_agent_excluded_from_active_actors_while_historical_runs_preserved(self) -> None:
        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))

        # Active actors derived from active_team: Eiren, Mr.Q, agy ONLY (no Copilot, no 0/0 completed card)
        agent_names = [a["name"] for a in payload["agents"]]
        self.assertEqual(agent_names, ["Eiren", "Mr.Q", "agy"])
        self.assertNotIn("Copilot", agent_names)
        for agent in payload["agents"]:
            self.assertNotIn("0/0", agent["current_activity"])

        # Removed agents metadata exposed honestly
        self.assertEqual(len(payload["removed_agents"]), 1)
        self.assertEqual(payload["removed_agents"][0]["name"], "Copilot")

        # Historical Copilot run is preserved in runs history and in B1's run history
        run_ids = [r["id"] for r in payload["runs"]]
        self.assertIn("20261017-232612-b1", run_ids)
        b1_run = next(r for r in payload["runs"] if r["id"] == "20261017-232612-b1")
        self.assertEqual(b1_run["owner"], "Copilot")
        self.assertTrue(b1_run["owner_removed"])

        # Fallback derivation when active_team is omitted: coordinator + current task owners
        plan_without_active_team = copy.deepcopy(SAMPLE_PLAN)
        del plan_without_active_team["active_team"]
        (self.root / "coordination/projects/project-bootstrapper/plan.json").write_text(
            json.dumps(plan_without_active_team, indent=2), encoding="utf-8"
        )
        status2, _, body2 = self._get("/api/state")
        self.assertEqual(status2, 200)
        payload2 = json.loads(body2.decode("utf-8"))
        self.assertEqual([a["name"] for a in payload2["agents"]], ["Eiren", "Mr.Q", "agy"])

    def test_running_record_with_nonexistent_pid_exposed_as_interrupted_without_accruing_time(self) -> None:
        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))

        runs_by_id = {r["id"]: r for r in payload["runs"]}

        # B1 run has PID 99999999 (does not exist):
        # - original execution_state is preserved as "running"
        # - observation_state is "interrupted" (or "unknown"), pid_alive is False
        # - elapsed_seconds is None (must NOT accrue live runtime forever)
        stale_run = runs_by_id["20261017-232612-b1"]
        self.assertEqual(stale_run["execution_state"], "running")
        self.assertFalse(stale_run["pid_alive"])
        self.assertIn(stale_run["observation_state"], ("interrupted", "unknown"))
        self.assertIsNone(stale_run["duration_seconds"])
        self.assertIsNone(stale_run["elapsed_seconds"])
        self.assertIn("99999999", stale_run["observation_label"])

        # V1 run has os.getpid() (exists locally):
        # - original execution_state is "running"
        # - observation_state notes PID presence without claiming it proves task work
        live_run = runs_by_id["20261017-232523-v1"]
        self.assertEqual(live_run["execution_state"], "running")
        self.assertTrue(live_run["pid_alive"])
        self.assertEqual(live_run["observation_state"], "pid_present_unverified")
        self.assertIsNotNone(live_run["elapsed_seconds"])
        self.assertIn("does not prove", live_run["observation_label"].lower())

        # Summary running_processes_count only counts runs whose PID is actually present
        self.assertEqual(payload["summary"]["running_processes_count"], 1)

    def test_malformed_task_dependencies_yields_degraded_state_without_server_exception(self) -> None:
        bad_plan = copy.deepcopy(SAMPLE_PLAN)
        bad_plan["tasks"][0]["dependencies"] = 12345  # integer instead of list
        bad_plan["tasks"][1]["evidence"] = 999  # integer instead of list
        (self.root / "coordination/projects/project-bootstrapper/plan.json").write_text(
            json.dumps(bad_plan, indent=2), encoding="utf-8"
        )

        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))
        self.assertIn(payload["status"], ("degraded", "error"))
        self.assertTrue(
            any("dependencies" in err["path"] or "dependencies" in err["error"] for err in payload["errors"]),
            f"Expected dependencies validation error in {payload['errors']}",
        )
        self.assertTrue(
            any("evidence" in err["path"] or "evidence" in err["error"] for err in payload["errors"]),
            f"Expected evidence validation error in {payload['errors']}",
        )

    def test_api_state_returns_honest_project_tasks_runs_and_review_separation(self) -> None:
        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertIn("observed_at", payload)
        self.assertTrue(payload["observed_at"].endswith("-03:00") or payload["observed_at"].endswith("-04:00"))
        self.assertEqual(payload["project"]["project"], "Agent Bootstrap")
        self.assertEqual(payload["project"]["coordinator"], "Eiren")
        self.assertEqual(payload["project"]["timezone"], "America/Santiago")

        # Counts: 1 accepted out of 6 total; no invented percentages
        self.assertEqual(payload["summary"]["accepted_count"], 1)
        self.assertEqual(payload["summary"]["total_count"], 6)
        self.assertNotIn("percentage", payload["summary"])

        # All phases A, B, C, D, E, Visibility represented
        phase_ids = [p["id"] for p in payload["phases"]]
        self.assertEqual(phase_ids, ["A", "B", "C", "D", "E", "Visibility"])

        tasks_by_id = {t["id"]: t for t in payload["tasks"]}
        self.assertEqual(set(tasks_by_id.keys()), {"A1", "B1", "C1", "D1", "E3", "V1"})

        # A1: process finished (exit 0), coordinator reviewed with changes_requested, state still 'dispatched'
        a1 = tasks_by_id["A1"]
        self.assertEqual(a1["state"], "dispatched")
        self.assertEqual(a1["review_status"], "changes_requested")
        self.assertEqual(a1["latest_run"]["execution_state"], "finished")
        self.assertEqual(a1["latest_run"]["exit_code"], 0)
        self.assertEqual(a1["latest_run"]["duration_seconds"], 180.0)
        self.assertIn("changes_requested", a1["review_label"].lower())

        # C1: unstarted planned task waiting on V1; no fake dates or activity
        c1 = tasks_by_id["C1"]
        self.assertEqual(c1["state"], "planned")
        self.assertEqual(c1["display_state"], "waiting")
        self.assertEqual(c1["unmet_dependencies"], ["V1"])
        self.assertIsNone(c1["latest_run"])
        self.assertIsNone(c1["reviewed_at"])

    def test_api_state_handles_missing_and_malformed_files_honestly(self) -> None:
        proj_dir = self.root / "coordination" / "projects" / "project-bootstrapper"
        runs_dir = proj_dir / "runs"

        # 1. Malformed run JSON and unknown execution_state -> degraded status, valid runs preserved
        (runs_dir / "corrupt.json").write_text("{not valid json", encoding="utf-8")
        bad_state_run = {
            "id": "20261017-232600-a1",
            "task_id": "A1",
            "owner": "Mr.Q",
            "started_at": "2026-10-17T23:26:00-03:00",
            "finished_at": None,
            "execution_state": "invented_state",
            "exit_code": None,
            "duration_seconds": None,
            "log_path": "coordination/projects/project-bootstrapper/logs/20261017-232600-a1.log",
            "pid": 111,
            "last_event_at": "2026-10-17T23:26:00-03:00",
        }
        (runs_dir / "bad_state.json").write_text(json.dumps(bad_state_run), encoding="utf-8")

        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(len(payload["runs"]), 3)
        self.assertTrue(any("corrupt.json" in err["path"] for err in payload["errors"]))
        self.assertTrue(any("bad_state.json" in err["path"] for err in payload["errors"]))

        # 2. Missing runs directory entirely -> never invents runs or crashes
        for f in runs_dir.iterdir():
            f.unlink()
        runs_dir.rmdir()
        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["runs"], [])
        self.assertFalse(runs_dir.exists(), "Read-only state check must not create directories")

        # 3. Malformed plan.json -> error status, not idle/success
        (proj_dir / "plan.json").write_text("{broken plan", encoding="utf-8")
        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "error")
        self.assertTrue(any("plan.json" in err["path"] for err in payload["errors"]))

        # 4. Missing plan.json -> error status
        (proj_dir / "plan.json").unlink()
        status, _, body = self._get("/api/state")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "error")
        self.assertTrue(any("plan.json" in err["path"] for err in payload["errors"]))

    def test_document_and_log_viewer_allowlist_and_traversal_protection(self) -> None:
        for allowed in (
            "coordination/assignments/bootstrap-a1.md",
            "coordination/inbox/20261017-233000-mrq-a1-review.md",
            "coordination/outbox/20261017-233000-mrq-a1-result.md",
            "coordination/projects/project-bootstrapper/logs/20261017-232520-a1.log",
        ):
            status, _, body = self._get(f"/api/file?path={quote(allowed)}")
            self.assertEqual(status, 200, f"Expected 200 for {allowed}")
            data = json.loads(body.decode("utf-8"))
            self.assertEqual(data["path"], allowed)
            self.assertTrue(len(data["content"]) > 0)

        status, _, _ = self._get("/api/file?path=coordination/assignments/nonexistent.md")
        self.assertEqual(status, 404)

        for forbidden in (
            "",
            "coordination/STATUS.md",
            "coordination/RULES.md",
            "coordination/projects/project-bootstrapper/plan.json",
            "coordination/projects/project-bootstrapper/runs/20261017-232520-a1.json",
            "README.md",
            "../README.md",
            "coordination/assignments/../../coordination/STATUS.md",
            "coordination/assignments/../STATUS.md",
            "coordination/assignments/./bootstrap-a1.md",
            "/etc/passwd",
            "coordination\\assignments\\..\\STATUS.md",
        ):
            status, _, _ = self._get(f"/api/file?path={quote(forbidden)}")
            self.assertEqual(status, 403, f"Expected 403 for {forbidden}")

        symlink_path = self.root / "coordination" / "assignments" / "escape.md"
        symlink_path.symlink_to(self.root / "coordination" / "STATUS.md")
        status, _, _ = self._get("/api/file?path=coordination/assignments/escape.md")
        self.assertEqual(status, 403)

        symlink_dir = self.root / "coordination" / "assignments" / "linked_dir"
        symlink_dir.symlink_to(self.root / "coordination")
        status, _, _ = self._get("/api/file?path=coordination/assignments/linked_dir/STATUS.md")
        self.assertEqual(status, 403)

    def test_static_serving_containment_and_read_only_methods(self) -> None:
        for route, expected_mime in (
            ("/", "text/html"),
            ("/index.html", "text/html"),
            ("/styles.css", "text/css"),
            ("/static/styles.css", "text/css"),
            ("/app.js", "application/javascript"),
            ("/static/app.js", "text/javascript" if False else "application/javascript"),
        ):
            status, headers, body = self._get(route)
            self.assertEqual(status, 200, f"Expected 200 for {route}")
            content_type = headers.get("Content-Type", "")
            self.assertIn(expected_mime, content_type)
            self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
            self.assertIn("default-src 'self'", headers.get("Content-Security-Policy", ""))
            self.assertTrue(len(body) > 0)

        for traversal in (
            "/../coordination/STATUS.md",
            "/%2e%2e/coordination/STATUS.md",
            "/static/../../server.py",
            "/static/%2e%2e/server.py",
            "/server.py",
            "/README.md",
        ):
            status, _, _ = self._get(traversal)
            self.assertEqual(status, 403, f"Expected 403 for {traversal}")

        js_code = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        self.assertNotIn(".innerHTML", js_code)
        self.assertNotIn("outerHTML", js_code)
        self.assertNotIn("insertAdjacentHTML", js_code)

        for method in ("POST", "PUT", "DELETE", "PATCH"):
            req = Request(f"http://127.0.0.1:{self.port}/api/state", data=b"{}", method=method)
            with self.assertRaises(HTTPError) as ctx:
                urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
