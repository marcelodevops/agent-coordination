/* Read-only client for Dupond.
 * Polls /api/state every 3 seconds. Uses textContent exclusively to prevent HTML injection.
 */
(function () {
  "use strict";

  const POLL_INTERVAL_MS = 3000;
  let currentState = null;
  let selectedTaskId = null;

  const el = {
    projectTitle: document.getElementById("project-title"),
    projectGoal: document.getElementById("project-goal"),
    connBadge: document.getElementById("conn-badge"),
    tzLabel: document.getElementById("tz-label"),
    observedAt: document.getElementById("observed-at"),
    lastRefresh: document.getElementById("last-refresh"),
    errorBanner: document.getElementById("error-banner"),
    errorBannerTitle: document.getElementById("error-banner-title"),
    errorBannerList: document.getElementById("error-banner-list"),
    metaCoordinator: document.getElementById("meta-coordinator"),
    metaActiveTeam: document.getElementById("meta-active-team"),
    metaRemovedWrap: document.getElementById("meta-removed-wrap"),
    metaRemovedAgents: document.getElementById("meta-removed-agents"),
    metaUpdated: document.getElementById("meta-updated"),
    metaWorkspace: document.getElementById("meta-workspace"),
    metaCoordRepo: document.getElementById("meta-coord-repo"),
    countAccepted: document.getElementById("count-accepted"),
    countDispatched: document.getElementById("count-dispatched"),
    countPlanned: document.getElementById("count-planned"),
    countProcesses: document.getElementById("count-processes"),
    agentsGrid: document.getElementById("agents-grid"),
    phasesFlow: document.getElementById("phases-flow"),
    tasksTbody: document.getElementById("tasks-tbody"),
    filterOwner: document.getElementById("filter-owner"),
    filterPhase: document.getElementById("filter-phase"),
    filterState: document.getElementById("filter-state"),
    taskDetailBox: document.getElementById("task-detail-box"),
    viewerFileTitle: document.getElementById("viewer-file-title"),
    viewerFileMeta: document.getElementById("viewer-file-meta"),
    manualPathInput: document.getElementById("manual-path-input"),
    manualPathBtn: document.getElementById("manual-path-btn"),
    fileViewerContent: document.getElementById("file-viewer-content"),
  };

  function clearChildren(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function makeElem(tag, className, text) {
    const node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = String(text);
    }
    return node;
  }

  function formatDuration(seconds) {
    if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) {
      return "—";
    }
    const s = Number(seconds);
    if (s < 60) {
      return s.toFixed(1) + "s";
    }
    const mins = Math.floor(s / 60);
    const rem = (s % 60).toFixed(0);
    return mins + "m " + rem + "s (" + s.toFixed(1) + "s)";
  }

  function formatNowSantiago() {
    try {
      return new Intl.DateTimeFormat("sv-SE", {
        timeZone: "America/Santiago",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZoneName: "shortOffset",
      }).format(new Date());
    } catch (_) {
      return new Date().toISOString();
    }
  }

  function updateOwnerFilterOptions(agents) {
    const previous = el.filterOwner.value || "ALL";
    const names = (agents || []).map(function (a) {
      return a.name;
    });
    clearChildren(el.filterOwner);
    const allOpt = makeElem("option", "", "All Active Owners");
    allOpt.value = "ALL";
    el.filterOwner.appendChild(allOpt);
    names.forEach(function (name) {
      const opt = makeElem("option", "", name);
      opt.value = name;
      el.filterOwner.appendChild(opt);
    });
    if (names.indexOf(previous) !== -1) {
      el.filterOwner.value = previous;
    } else {
      el.filterOwner.value = "ALL";
    }
  }

  function createTaskStateBadge(task) {
    if (task.state === "accepted") {
      return makeElem("span", "badge badge-accepted", "✓ ACCEPTED");
    }
    if (task.review_status === "changes_requested") {
      return makeElem(
        "span",
        "badge badge-warn",
        "▲ DISPATCHED · CHANGES REQUESTED"
      );
    }
    if (task.state === "dispatched") {
      return makeElem("span", "badge badge-dispatched", "◆ DISPATCHED · REVIEW PENDING");
    }
    if (task.display_state === "waiting") {
      return makeElem("span", "badge badge-waiting", "⏳ WAITING ON DEPS");
    }
    if (task.state === "planned") {
      return makeElem("span", "badge badge-planned", "○ PLANNED");
    }
    return makeElem(
      "span",
      "badge badge-unknown",
      "? " + String(task.state || "UNKNOWN").toUpperCase()
    );
  }

  function createProcessStateBadge(task) {
    const run = task.latest_run;
    if (!run) {
      if (task.state === "planned") {
        return makeElem("span", "badge badge-planned", "— NOT STARTED (PLANNED/WAITING)");
      }
      return makeElem("span", "badge badge-waiting", "— NO PROCESS RUN RECORDED");
    }
    const st = run.execution_state;
    const obs = run.observation_state;

    if (st === "running") {
      if (obs === "pid_present_unverified") {
        return makeElem(
          "span",
          "badge badge-running",
          "▶ REPORTED RUNNING · PID " + (run.pid ?? "—") + " PRESENT (UNVERIFIED)"
        );
      }
      return makeElem(
        "span",
        "badge badge-warn",
        "⚠ REPORTED RUNNING · PID " + (run.pid ?? "—") + " GONE (" + String(obs || "INTERRUPTED").toUpperCase() + ")"
      );
    }
    if (st === "finished") {
      if (task.state === "accepted") {
        return makeElem("span", "badge badge-ok", "● PROCESS FINISHED (EXIT 0)");
      }
      return makeElem(
        "span",
        "badge badge-finished-unaccepted",
        "● PROCESS EXITED (0) · NOT ACCEPTED YET"
      );
    }
    if (st === "failed" || st === "launch_failed") {
      return makeElem(
        "span",
        "badge badge-error",
        "✖ PROCESS " + st.toUpperCase() + " (EXIT " + (run.exit_code ?? "—") + ")"
      );
    }
    return makeElem("span", "badge badge-unknown", "? PROCESS " + String(st));
  }

  function setConnectionStatus(kind, message, errorsList) {
    el.connBadge.className = "badge";
    if (kind === "ok") {
      el.connBadge.classList.add("badge-ok");
      el.connBadge.textContent = "● LIVE · STATE OK";
      el.errorBanner.hidden = true;
    } else if (kind === "degraded") {
      el.connBadge.classList.add("badge-warn");
      el.connBadge.textContent = "▲ LIVE · DEGRADED DATA";
      el.errorBanner.className = "alert-banner alert-warn";
      el.errorBanner.hidden = false;
      el.errorBannerTitle.textContent = message || "Some coordination files could not be parsed:";
      clearChildren(el.errorBannerList);
      (errorsList || []).forEach(function (item) {
        const li = makeElem("li", "", (item.path ? item.path + ": " : "") + item.error);
        el.errorBannerList.appendChild(li);
      });
    } else {
      el.connBadge.classList.add("badge-error");
      el.connBadge.textContent = "✖ ERROR · STATE UNKNOWN";
      el.errorBanner.className = "alert-banner alert-error";
      el.errorBanner.hidden = false;
      el.errorBannerTitle.textContent =
        message || "Unable to load valid state (unknown state is not idle or success):";
      clearChildren(el.errorBannerList);
      (errorsList || []).forEach(function (item) {
        const li = makeElem("li", "", (item.path ? item.path + ": " : "") + item.error);
        el.errorBannerList.appendChild(li);
      });
    }
  }

  function renderAgents(agents) {
    clearChildren(el.agentsGrid);
    (agents || []).forEach(function (agent) {
      const card = makeElem("article", "agent-card");

      const top = makeElem("div", "agent-top");
      const nameWrap = makeElem("div", "");
      nameWrap.appendChild(makeElem("span", "agent-name", agent.name));
      nameWrap.appendChild(makeElem("span", "agent-role", "(" + agent.role + ")"));
      top.appendChild(nameWrap);

      let badgeClass = "badge badge-waiting";
      let badgeLabel = "WAITING / PLANNED";
      if (agent.status === "running") {
        badgeClass = "badge badge-running";
        badgeLabel = "▶ PID PRESENT · RUNNING";
      } else if (agent.status === "awaiting_review") {
        badgeClass = "badge badge-dispatched";
        badgeLabel = "◆ DISPATCHED · REVIEW PENDING";
      } else if (agent.status === "coordinating") {
        badgeClass = "badge badge-coordinating";
        badgeLabel = "◈ COORDINATING & REVIEWING";
      } else if (agent.status === "completed") {
        badgeClass = "badge badge-accepted";
        badgeLabel = "✓ ALL ACCEPTED";
      }
      top.appendChild(makeElem("span", badgeClass, badgeLabel));
      card.appendChild(top);

      card.appendChild(makeElem("div", "agent-activity", agent.current_activity));

      const runBox = makeElem("div", "agent-run-box");
      if (agent.latest_run) {
        const r = agent.latest_run;
        const durText =
          r.duration_seconds !== null
            ? "duration " + formatDuration(r.duration_seconds)
            : r.elapsed_seconds !== null
            ? "elapsed " + formatDuration(r.elapsed_seconds)
            : "no verified duration (PID gone)";
        runBox.textContent =
          "Latest process: " +
          r.task_id +
          " · worker_report=" +
          r.execution_state +
          " · observed=" +
          r.observation_state +
          " · start " +
          (r.started_at || "—") +
          " · " +
          durText;
      } else if (agent.role === "Coordinator") {
        runBox.textContent =
          "Owns shared rules, assignments, STATUS.md, and final review acceptance.";
      } else {
        runBox.textContent = "No worker CLI run recorded yet.";
      }
      card.appendChild(runBox);

      const chipRow = makeElem("div", "agent-tasks-row");
      (agent.owned_task_ids || []).forEach(function (tid) {
        const chip = makeElem("button", "task-chip", tid);
        chip.type = "button";
        chip.addEventListener("click", function () {
          selectTask(tid);
        });
        chipRow.appendChild(chip);
      });
      card.appendChild(chipRow);

      el.agentsGrid.appendChild(card);
    });
  }

  function renderPhases(phases) {
    clearChildren(el.phasesFlow);
    (phases || []).forEach(function (phase) {
      const card = makeElem("div", "phase-card");
      const header = makeElem("div", "phase-header");
      header.appendChild(makeElem("span", "phase-title", phase.label));
      header.appendChild(
        makeElem(
          "span",
          "phase-count",
          phase.accepted_count + " / " + phase.total_count + " accepted"
        )
      );
      card.appendChild(header);
      card.appendChild(makeElem("div", "phase-desc", phase.description));

      const list = makeElem("div", "phase-task-list");
      (phase.tasks || []).forEach(function (t) {
        const btn = makeElem("button", "phase-task-item");
        btn.type = "button";
        btn.addEventListener("click", function () {
          selectTask(t.id);
        });

        const top = makeElem("div", "phase-task-top");
        top.appendChild(makeElem("strong", "", t.id + " · " + t.owner));
        top.appendChild(
          makeElem("span", "badge badge-" + t.display_state, t.display_state.toUpperCase())
        );
        btn.appendChild(top);

        btn.appendChild(makeElem("div", "", t.title));

        const depsText =
          t.dependencies && t.dependencies.length > 0
            ? "Waits for: " + t.dependencies.join(", ")
            : "Ready (no dependencies)";
        const procText = t.observation_state
          ? "Observed: " + t.observation_state
          : "Process: not started";
        btn.appendChild(makeElem("div", "phase-task-meta", depsText + " · " + procText));

        list.appendChild(btn);
      });
      card.appendChild(list);
      el.phasesFlow.appendChild(card);
    });
  }

  function renderTasksTable(tasks) {
    clearChildren(el.tasksTbody);
    const ownerFilter = el.filterOwner.value;
    const phaseFilter = el.filterPhase.value;
    const stateFilter = el.filterState.value;

    const filtered = (tasks || []).filter(function (t) {
      if (ownerFilter !== "ALL" && t.owner !== ownerFilter) {
        return false;
      }
      if (phaseFilter !== "ALL" && t.phase !== phaseFilter) {
        return false;
      }
      if (stateFilter !== "ALL" && t.state !== stateFilter) {
        return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      const tr = makeElem("tr", "");
      const td = makeElem("td", "muted-note", "No tasks match the current filter.");
      td.colSpan = 7;
      tr.appendChild(td);
      el.tasksTbody.appendChild(tr);
      return;
    }

    filtered.forEach(function (task) {
      const tr = makeElem("tr", task.id === selectedTaskId ? "selected-row" : "");
      tr.addEventListener("click", function () {
        selectTask(task.id);
      });

      // 1. Task ID + Title
      const tdId = makeElem("td", "task-id-cell", task.id);
      tdId.appendChild(makeElem("span", "task-title-sub", task.title));
      tr.appendChild(tdId);

      // 2. Phase
      tr.appendChild(makeElem("td", "", task.phase));

      // 3. Owner
      const tdOwner = makeElem("td", "", task.owner);
      if (task.previous_owner) {
        tdOwner.appendChild(
          makeElem("span", "cell-subnote", "Reassigned from " + task.previous_owner)
        );
      }
      tr.appendChild(tdOwner);

      // 4. Dependencies
      const tdDeps = makeElem("td", "");
      if (!task.dependencies || task.dependencies.length === 0) {
        tdDeps.textContent = "None";
      } else {
        tdDeps.textContent = task.dependencies.join(", ");
        if (task.unmet_dependencies && task.unmet_dependencies.length > 0) {
          tdDeps.appendChild(
            makeElem("span", "cell-subnote", "Unaccepted: " + task.unmet_dependencies.join(", "))
          );
        } else {
          tdDeps.appendChild(makeElem("span", "cell-subnote", "All dependencies accepted"));
        }
      }
      tr.appendChild(tdDeps);

      // 5. Coordinator Task & Review State
      const tdCoord = makeElem("td", "");
      tdCoord.appendChild(createTaskStateBadge(task));
      tdCoord.appendChild(makeElem("span", "cell-subnote", task.review_label));
      if (task.reviewed_at) {
        tdCoord.appendChild(makeElem("span", "cell-subnote", "Reviewed at: " + task.reviewed_at));
      }
      tr.appendChild(tdCoord);

      // 6. Worker Process & Observation (separate from review acceptance)
      const tdProc = makeElem("td", "");
      tdProc.appendChild(createProcessStateBadge(task));
      if (task.latest_run) {
        tdProc.appendChild(
          makeElem(
            "span",
            "cell-subnote",
            "Run " +
              task.latest_run.id +
              " · " +
              task.latest_run.observation_label
          )
        );
      } else if (task.historical_runs && task.historical_runs.length > 0) {
        tdProc.appendChild(
          makeElem(
            "span",
            "cell-subnote",
            task.historical_runs.length +
              " historical run(s) from removed/prior owner preserved in history"
          )
        );
      }
      tr.appendChild(tdProc);

      // 7. Timing (America/Santiago) — never fake dates or accrue dead-PID runtime
      const tdTime = makeElem("td", "");
      if (!task.latest_run) {
        tdTime.textContent = "Not executed";
        tdTime.appendChild(
          makeElem("span", "cell-subnote", "Planned / waiting — no start or end time")
        );
      } else {
        const r = task.latest_run;
        tdTime.appendChild(makeElem("div", "", "Start: " + (r.started_at || "—")));
        tdTime.appendChild(
          makeElem(
            "div",
            "",
            "End: " +
              (r.finished_at ||
                (r.observation_state === "pid_present_unverified"
                  ? "running (PID present)"
                  : "not recorded (" + r.observation_state + ")"))
          )
        );
        if (r.duration_seconds !== null) {
          tdTime.appendChild(
            makeElem("span", "cell-subnote", "Measured duration: " + formatDuration(r.duration_seconds))
          );
        } else if (r.elapsed_seconds !== null) {
          tdTime.appendChild(
            makeElem("span", "cell-subnote", "Elapsed since start: " + formatDuration(r.elapsed_seconds))
          );
        } else {
          tdTime.appendChild(
            makeElem("span", "cell-subnote", "Duration unknown (process PID gone before finish)")
          );
        }
      }
      tr.appendChild(tdTime);

      el.tasksTbody.appendChild(tr);
    });
  }

  function renderTaskDetail(task) {
    clearChildren(el.taskDetailBox);
    if (!task) {
      el.taskDetailBox.appendChild(
        makeElem(
          "p",
          "muted-note",
          "Select a task to inspect its coordinator state, process runs, assignment, inbox/outbox messages, and logs."
        )
      );
      return;
    }

    el.taskDetailBox.appendChild(
      makeElem("h3", "detail-title", task.id + " · " + task.title)
    );

    const grid = makeElem("div", "detail-grid");
    const fields = [
      ["Owner", task.owner + (task.previous_owner ? " (previously " + task.previous_owner + ")" : "")],
      ["Phase", task.phase],
      ["Coordinator State", task.state + " (" + task.display_state + ")"],
      ["Review Status", task.review_label],
      ["Reviewed At (America/Santiago)", task.reviewed_at || "Not reviewed yet"],
      [
        "Dependencies",
        task.dependencies && task.dependencies.length > 0
          ? task.dependencies.join(", ")
          : "None",
      ],
    ];
    fields.forEach(function (pair) {
      const item = makeElem("div", "detail-item");
      item.appendChild(makeElem("strong", "", pair[0]));
      item.appendChild(makeElem("span", "", pair[1]));
      grid.appendChild(item);
    });
    el.taskDetailBox.appendChild(grid);

    if (task.notes) {
      const notesBox = makeElem("div", "agent-run-box", "Coordinator notes: " + task.notes);
      el.taskDetailBox.appendChild(notesBox);
    }

    if (task.review_history && task.review_history.length > 0) {
      const rhGroup = makeElem("div", "doc-links-group");
      rhGroup.appendChild(makeElem("div", "doc-links-title", "Coordinator Review History"));
      task.review_history.forEach(function (rh) {
        rhGroup.appendChild(
          makeElem(
            "div",
            "agent-run-box",
            (rh.at || "—") + " · decision=" + rh.decision + " · " + rh.reason
          )
        );
      });
      el.taskDetailBox.appendChild(rhGroup);
    }

    // Runs history (including historical runs from removed agents)
    const runsGroup = makeElem("div", "doc-links-group");
    runsGroup.appendChild(
      makeElem(
        "div",
        "doc-links-title",
        "Worker CLI Run History (" + (task.runs ? task.runs.length : 0) + ")"
      )
    );
    if (!task.runs || task.runs.length === 0) {
      runsGroup.appendChild(
        makeElem(
          "p",
          "muted-note",
          "No worker process runs recorded for this task (planned / waiting)."
        )
      );
    } else {
      task.runs.forEach(function (r) {
        const prefix = r.owner_removed ? "[HISTORICAL · REMOVED OWNER " + r.owner + "] " : "";
        const durPart =
          r.duration_seconds !== null
            ? "duration=" + formatDuration(r.duration_seconds)
            : r.elapsed_seconds !== null
            ? "elapsed=" + formatDuration(r.elapsed_seconds)
            : "duration=unknown (PID gone)";
        const line = makeElem(
          "div",
          "agent-run-box",
          prefix +
            r.id +
            " · owner=" +
            r.owner +
            " · worker_report=" +
            r.execution_state +
            " · observed=" +
            r.observation_state +
            " · exit=" +
            (r.exit_code ?? "—") +
            " · start=" +
            (r.started_at || "—") +
            " · end=" +
            (r.finished_at || "none") +
            " · " +
            durPart
        );
        runsGroup.appendChild(line);
      });
    }
    el.taskDetailBox.appendChild(runsGroup);

    // Allowlisted documents & logs buttons
    const docsGroup = makeElem("div", "doc-links-group");
    docsGroup.appendChild(
      makeElem("div", "doc-links-title", "Allowlisted Assignment, Evidence & Logs")
    );
    const btnList = makeElem("div", "doc-buttons-list");

    function addFileButton(label, path) {
      const b = makeElem("button", "view-btn", label);
      b.type = "button";
      b.addEventListener("click", function () {
        loadAllowlistedFile(path);
      });
      btnList.appendChild(b);
    }

    if (task.assignment) {
      addFileButton("Assignment: " + task.assignment, task.assignment);
    }
    (task.evidence_files || []).forEach(function (ev) {
      addFileButton("Plan Evidence: " + ev.path, ev.path);
    });
    (task.discovered_messages || []).forEach(function (msg) {
      addFileButton(msg.kind.toUpperCase() + ": " + msg.name, msg.path);
    });
    (task.runs || []).forEach(function (r) {
      if (r.log_path) {
        const tag = r.owner_removed ? "Historical Log (" + r.owner + "): " : "Log: ";
        addFileButton(tag + r.id + ".log", r.log_path);
      }
    });

    if (!btnList.firstChild) {
      docsGroup.appendChild(
        makeElem(
          "p",
          "muted-note",
          "No assignment, evidence, or log files linked yet for this task."
        )
      );
    } else {
      docsGroup.appendChild(btnList);
    }
    el.taskDetailBox.appendChild(docsGroup);
  }

  function selectTask(taskId) {
    selectedTaskId = taskId;
    if (!currentState || !currentState.tasks) {
      return;
    }
    renderTasksTable(currentState.tasks);
    const found = currentState.tasks.find(function (t) {
      return t.id === taskId;
    });
    renderTaskDetail(found || null);
  }

  async function loadAllowlistedFile(path) {
    if (!path) {
      return;
    }
    el.manualPathInput.value = path;
    el.viewerFileTitle.textContent = path;
    el.viewerFileMeta.textContent = "Loading…";
    el.fileViewerContent.textContent = "Fetching " + path + "…";

    try {
      const resp = await fetch("/api/file?path=" + encodeURIComponent(path), {
        cache: "no-store",
      });
      const data = await resp.json();
      if (!resp.ok || !data.ok) {
        el.viewerFileMeta.textContent = "HTTP " + resp.status + " · Refused / Unavailable";
        el.fileViewerContent.textContent =
          "Error loading file (" + resp.status + "): " + (data.error || "Unknown error");
        return;
      }
      el.viewerFileTitle.textContent = data.path;
      el.viewerFileMeta.textContent =
        data.size_bytes +
        " bytes · modified " +
        (data.modified_at || "—") +
        (data.truncated ? " (TRUNCATED)" : "");
      el.fileViewerContent.textContent = data.content || "(empty file)";
    } catch (err) {
      el.viewerFileMeta.textContent = "Network error";
      el.fileViewerContent.textContent = "Failed to fetch allowlisted file: " + String(err);
    }
  }

  async function fetchState() {
    try {
      const resp = await fetch("/api/state", { cache: "no-store" });
      const data = await resp.json();
      el.lastRefresh.textContent = formatNowSantiago();

      if (!resp.ok || !data.ok) {
        setConnectionStatus(
          "error",
          "Coordination state is unavailable or invalid (HTTP " + resp.status + "):",
          data.errors || [{ path: "plan.json", error: "Failed to read valid coordination state." }]
        );
        if (data.observed_at) {
          el.observedAt.textContent = data.observed_at;
        }
        return;
      }

      currentState = data;
      el.observedAt.textContent = data.observed_at || "—";
      el.tzLabel.textContent = data.timezone || "America/Santiago";

      if (data.status === "degraded") {
        setConnectionStatus(
          "degraded",
          "State loaded with warnings (some fields or files malformed):",
          data.errors
        );
      } else {
        setConnectionStatus("ok", "", []);
      }

      if (data.project) {
        el.projectTitle.textContent =
          "Dupond · " + data.project.project;
        el.projectGoal.textContent = data.project.goal;
        el.metaCoordinator.textContent = data.project.coordinator;
        el.metaActiveTeam.textContent = (data.project.active_team || []).join(", ") || "—";
        el.metaUpdated.textContent = data.project.updated_at || "—";
        el.metaWorkspace.textContent = data.project.workspace;
        el.metaCoordRepo.textContent = data.project.coordination_repo;
      }

      if (data.removed_agents && data.removed_agents.length > 0) {
        el.metaRemovedWrap.hidden = false;
        el.metaRemovedAgents.textContent = data.removed_agents
          .map(function (r) {
            return r.name;
          })
          .join(", ");
      } else {
        el.metaRemovedWrap.hidden = true;
      }

      const sum = data.summary || {};
      el.countAccepted.textContent =
        (sum.accepted_count ?? 0) + " / " + (sum.total_count ?? 0) + " tasks";
      el.countDispatched.textContent = (sum.dispatched_count ?? 0) + " tasks";
      el.countPlanned.textContent = (sum.planned_count ?? 0) + " tasks";
      const totalRuns = (data.runs || []).length;
      const runningCount = sum.running_processes_count ?? 0;
      const interruptedCount = sum.interrupted_processes_count ?? 0;
      el.countProcesses.textContent =
        runningCount +
        " PID present · " +
        interruptedCount +
        " interrupted · " +
        totalRuns +
        " total";

      updateOwnerFilterOptions(data.agents || []);
      renderAgents(data.agents || []);
      renderPhases(data.phases || []);

      if (!selectedTaskId && data.tasks && data.tasks.length > 0) {
        const firstDispatched = data.tasks.find(function (t) {
          return t.state === "dispatched";
        });
        selectedTaskId = (firstDispatched || data.tasks[0]).id;
      }
      renderTasksTable(data.tasks || []);
      const currentTask = (data.tasks || []).find(function (t) {
        return t.id === selectedTaskId;
      });
      renderTaskDetail(currentTask || null);
    } catch (err) {
      el.lastRefresh.textContent = formatNowSantiago() + " (failed)";
      setConnectionStatus("error", "Connection error polling /api/state:", [
        { path: "/api/state", error: String(err) },
      ]);
    }
  }

  el.filterOwner.addEventListener("change", function () {
    if (currentState) {
      renderTasksTable(currentState.tasks);
    }
  });
  el.filterPhase.addEventListener("change", function () {
    if (currentState) {
      renderTasksTable(currentState.tasks);
    }
  });
  el.filterState.addEventListener("change", function () {
    if (currentState) {
      renderTasksTable(currentState.tasks);
    }
  });
  el.manualPathBtn.addEventListener("click", function () {
    loadAllowlistedFile(el.manualPathInput.value.trim());
  });
  el.manualPathInput.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      loadAllowlistedFile(el.manualPathInput.value.trim());
    }
  });

  fetchState();
  setInterval(fetchState, POLL_INTERVAL_MS);
})();
