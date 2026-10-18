# V1 — coordinator review notes for final delivery

Author: Eiren
Assignment: [V1](../assignments/bootstrap-v1.md)
Intended recipient: agy
Kind: review feedback
Dependencies: user removed Copilot while this assignment was executing
Requested decision/result: address these before coordinator acceptance; keep dashboard scope bounded.

1. The latest plan.json includes active_team=[Eiren, Mr.Q, agy] and removed_agents metadata. Copilot must not appear as an active actor or as completed 0/0. Preserve its old runs only in history. Derive actor cards from active_team when present, otherwise coordinator plus task owners. Add a test for removal with retained historical runs.
2. A run marked running whose process has disappeared must not accrue live runtime forever as if verified active. Expose an observation state (unknown/interrupted if PID is gone) without editing historical records or claiming PID existence proves task work. Preserve original execution_state as the worker report and label the observation clearly. Add a test with a nonexistent PID.
3. Valid JSON with a malformed task dependencies field (e.g. integer) should yield a degraded/error state instead of throwing an unhandled server exception. Add a small test at this data boundary.

The server has been launched by Eiren on 127.0.0.1:8787 for integration checks; do not create another persistent server. Eiren will restart after your server changes. This note is not a claim that you have received a wake-up; follow-up dispatch will be explicit if your current run does not consume it.

4. Remove the test that asserts the live repo always contains exactly fifteen tasks and four hardcoded actors. It couples the test suite to changing production data and currently blesses the removed Copilot card. Keep runtime integration checks as coordinator evidence; unit tests should use temporary fixtures. Also derive owner filter/header labels from the active team, rather than hardcoding Copilot in HTML.
