"""Run one explicitly assigned local worker and record actual execution timing.

This records process state only. Eiren owns task acceptance in plan.json/STATUS.md.
"""
from __future__ import annotations
import argparse
import fcntl
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
WORK = Path('/Users/mac/ops/worktrees/project-bootstrapper-plan')

def now() -> str:
    return datetime.now(ZoneInfo('America/Santiago')).isoformat(timespec='seconds')

def save(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', help='ID of an explicitly dispatched assignment in plan.json')
    parser.add_argument('--resume', help='Existing worker session/conversation ID for a reviewed correction')
    parser.add_argument('--feedback', help='Repo-relative coordinator feedback file to address')
    args = parser.parse_args()
    plan = json.loads((PROJECT / 'plan.json').read_text())
    task = next((t for t in plan['tasks'] if t['id'] == args.task), None)
    if task is None:
        parser.error('Unknown task ID')
    if task['state'] != 'dispatched':
        parser.error('Eiren must explicitly mark this assignment dispatched before launch')
    accepted = {t['id'] for t in plan['tasks'] if t['state'] == 'accepted'}
    if any(dependency not in accepted for dependency in task['dependencies']):
        parser.error('All dependencies must be accepted by Eiren before launch')
    if task['owner'] not in ('Mr.Q', 'agy'):
        parser.error('Only the currently authorized workers Mr.Q and agy may be launched')
    if not task.get('assignment'):
        parser.error('No bounded assignment has been issued for this task')
    assignment = (ROOT / task['assignment']).resolve()
    if not assignment.is_relative_to(ROOT / 'coordination/assignments') or not assignment.is_file():
        parser.error('Assignment must exist within coordination/assignments')
    prompt = (f'Execute only the bounded assignment at {assignment}. Read it and its mandatory inputs first. '
              'The user authorized this assignment. You are not alone; preserve other workers edits. '
              'Do not ask for planning approval. Implement within ownership, run tests, and write BOTH required '
              'outbox result and inbox review request. Do not commit/push/publish or create other agents. '
              'If blocked, write a blocker with the actual error instead of inventing completion.')
    if args.feedback:
        feedback = (ROOT / args.feedback).resolve()
        if not feedback.is_relative_to(ROOT / 'coordination/inbox') or not feedback.is_file():
            parser.error('Feedback must exist within coordination/inbox')
        prompt += f' This is a correction round. Read and address all findings in {feedback}; write NEW paired result/review messages with updated test evidence.'
    if task['owner'] == 'Mr.Q':
        cmd = ['/Users/mac/.local/bin/qodercli', '--cwd', str(WORK), '--add-dir', str(ROOT),
               '--permission-mode', 'auto', '-p', prompt]
        cwd = WORK
    else:
        cmd = ['/Users/mac/.local/bin/agy', '--add-dir', str(ROOT),
               '--add-dir', str(WORK), '--print-timeout', '15m', '-p', prompt]
        cwd = ROOT if args.task == 'V1' else WORK
    if args.resume:
        flag = '--resume' if task['owner'] == 'Mr.Q' else '--conversation'
        cmd[1:1] = [flag, args.resume]
    runs = PROJECT / 'runs'; logs = PROJECT / 'logs'
    runs.mkdir(exist_ok=True); logs.mkdir(exist_ok=True)
    # One process per assignment; distinct assignments remain independent.
    lock = (runs / f'.{args.task}.lock').open('a')
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('This assignment already has an active launch')
    for existing in runs.glob('*.json'):
        try:
            record = json.loads(existing.read_text())
        except (OSError, ValueError):
            parser.error(f'Cannot verify prior run record: {existing.name}')
        if record.get('task_id') == args.task and record.get('execution_state') == 'running':
            pid = record.get('pid')
            if pid:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    parser.error('A prior execution is still active; review it before relaunching')
    run_id = datetime.now(ZoneInfo('America/Santiago')).strftime('%Y%m%d-%H%M%S') + '-' + args.task.lower()
    dest = runs / f'{run_id}.json'; log_path = logs / f'{run_id}.log'
    if dest.exists():
        parser.error('run id already exists; retry after this second')
    data = dict(id=run_id, task_id=args.task, owner=task['owner'], started_at=now(),
                finished_at=None, execution_state='running', exit_code=None, duration_seconds=None,
                log_path=str(log_path.relative_to(ROOT)), pid=None, last_event_at=now())
    start = time.monotonic()
    try:
        with log_path.open('w') as output:
            process = subprocess.Popen(cmd, cwd=cwd, stdout=output, stderr=subprocess.STDOUT)
            data['pid'] = process.pid
            save(dest, data)
            print(f'{args.task}: launched {task["owner"]}, PID {process.pid}, run {run_id}', flush=True)
            code = process.wait()
        data['exit_code'] = code
        data['execution_state'] = 'finished' if code == 0 else 'failed'
    except OSError as exc:
        data['execution_state'] = 'launch_failed'
        data['exit_code'] = 127
        log_path.write_text(f'Worker launch failed: {exc}\n')
    finally:
        data['finished_at'] = now()
        data['last_event_at'] = data['finished_at']
        data['duration_seconds'] = round(time.monotonic() - start, 3)
        save(dest, data)
    print(f'{args.task}: process {data["execution_state"]} in {data["duration_seconds"]}s; coordinator review pending', flush=True)
    return int(data['exit_code'] or 0)

if __name__ == '__main__':
    sys.exit(main())
