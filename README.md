# Agent coordination

A basic shared workspace for assignments, questions, results and coordinator decisions. The goal is to eliminate copying prompts and reports between agents while keeping one agreed approach.

Start with [STARTING-POINT.md](STARTING-POINT.md), then [coordination/RULES.md](coordination/RULES.md) and [coordination/STATUS.md](coordination/STATUS.md).

The repository contains assignments, worker results, coordinator decisions, an explicit worker launcher and a local read-only dashboard. A coordinator dispatches and reviews each task; files and the dashboard do not wake agents or accept work automatically.

## Current Bootstrap coordination dashboard

The implemented read-only dashboard lives in [dashboard/](dashboard/README.md). Start from this repository with `python3 -m dashboard --port 8787` and open http://127.0.0.1:8787/. It polls execution records and coordinator decisions every three seconds; it does not dispatch or accept work autonomously. The Bootstrap source of truth is [plan.json](coordination/projects/project-bootstrapper/plan.json), with review evidence in inbox/outbox and decisions in STATUS.md.
