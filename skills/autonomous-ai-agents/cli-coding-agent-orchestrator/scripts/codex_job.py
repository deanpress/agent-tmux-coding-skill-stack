#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DEFAULT_HERMES_HOME = Path(__file__).resolve().parents[4]
HERMES_HOME = Path(os.environ.get('HERMES_HOME', str(DEFAULT_HERMES_HOME))).expanduser().resolve()
LOG_ROOT = HERMES_HOME / 'agent-supervisor'
SUPERVISOR = Path(__file__).resolve().parent / 'tmux_cli_supervisor.py'
JOBS_DIR = LOG_ROOT / 'jobs'


def sanitize(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return value or 'job'


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + '\n')


def tmux_has(session: str) -> bool:
    return subprocess.run(['tmux', 'has-session', '-t', session], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def tmux_capture(session: str, start: str = '-120') -> str:
    result = subprocess.run(
        ['tmux', 'capture-pane', '-pt', session, '-S', start],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode != 0:
        return ''
    return result.stdout


def tmux_send(session: str, prompt: str) -> None:
    subprocess.run(['tmux', 'send-keys', '-t', session, prompt, 'C-m'], check=True)


def kill_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def resolve_job(name: str) -> Path:
    path = JOBS_DIR / f'{name}.json'
    if not path.exists():
        raise SystemExit(f'job not found: {name}')
    return path


def load_job(name: str) -> dict:
    return read_json(resolve_job(name))


def latest_jobs():
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(JOBS_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)


def cmd_start(args) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.is_dir():
        raise SystemExit(f'workdir does not exist: {workdir}')
    prompt = args.prompt
    prompt_file = Path(args.prompt_file).resolve() if args.prompt_file else None
    if prompt_file and not prompt_file.exists():
        raise SystemExit(f'prompt file does not exist: {prompt_file}')

    base = args.name or f"{sanitize(workdir.name)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    job = sanitize(base)
    session = args.session or f'ai-codex-{job}'
    job_file = JOBS_DIR / f'{job}.json'
    if job_file.exists():
        raise SystemExit(f'job already exists: {job}')

    run_dir = LOG_ROOT / session
    run_log = run_dir / 'run.log'
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(SUPERVISOR),
        '--agent', 'codex',
        '--workdir', str(workdir),
        '--session', session,
        '--poll-seconds', str(args.poll_seconds),
        '--notify-on-state',
    ]
    if args.ready_timeout is not None:
        cmd += ['--ready-timeout', str(args.ready_timeout)]
    if args.substantial_job:
        cmd.append('--substantial-job')
    if args.require_commit:
        cmd.append('--require-commit')
    if args.extra_launch_args:
        cmd += ['--extra-launch-args', args.extra_launch_args]
    if prompt_file:
        cmd += ['--prompt-file', str(prompt_file)]
    else:
        cmd += ['--prompt', prompt]

    with run_log.open('ab') as handle:
        proc = subprocess.Popen(cmd, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)

    payload = {
        'job': job,
        'session': session,
        'workdir': str(workdir),
        'prompt_file': str(prompt_file) if prompt_file else None,
        'prompt_inline': None if prompt_file else prompt,
        'substantial_job': args.substantial_job,
        'require_commit': args.require_commit,
        'ready_timeout': args.ready_timeout,
        'poll_seconds': args.poll_seconds,
        'extra_launch_args': args.extra_launch_args,
        'created_at': time.time(),
        'supervisor_pid': proc.pid,
        'run_dir': str(run_dir),
        'run_log': str(run_log),
        'status_file': str(run_dir / 'status.json'),
        'events_file': str(run_dir / 'events.jsonl'),
    }
    write_json(job_file, payload)
    print(json.dumps({'job': job, 'session': session, 'supervisor_pid': proc.pid, 'run_dir': str(run_dir)}, ensure_ascii=False))
    return 0


def summarize(job_meta: dict) -> dict:
    status_path = Path(job_meta['status_file'])
    status = read_json(status_path) if status_path.exists() else {}
    pid = job_meta.get('supervisor_pid')
    session = job_meta['session']
    return {
        'job': job_meta['job'],
        'session': session,
        'workdir': job_meta['workdir'],
        'supervisor_pid': pid,
        'supervisor_alive': process_alive(pid) if pid else False,
        'tmux_session_alive': tmux_has(session),
        'state': status.get('state', 'unknown'),
        'completed': status.get('completed', False),
        'require_commit': job_meta.get('require_commit', False),
        'commit_verified': status.get('commit_verified', False),
        'run_dir': job_meta['run_dir'],
    }


def cmd_status(args) -> int:
    meta = load_job(args.name)
    print(json.dumps(summarize(meta), ensure_ascii=False, indent=2))
    return 0


def cmd_list(args) -> int:
    rows = []
    for path in latest_jobs()[: args.limit]:
        meta = read_json(path)
        rows.append(summarize(meta))
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args) -> int:
    meta = load_job(args.name)
    run_log = Path(meta['run_log'])
    if not run_log.exists():
        raise SystemExit('run log not found')
    lines = run_log.read_text(encoding='utf-8', errors='ignore').splitlines()
    for line in lines[-args.lines:]:
        print(line)
    return 0


def cmd_checkin(args) -> int:
    meta = load_job(args.name)
    payload = summarize(meta)
    run_log = Path(meta['run_log'])
    status_path = Path(meta['status_file'])
    payload['status'] = read_json(status_path) if status_path.exists() else {}
    payload['pane_capture'] = tmux_capture(meta['session'], args.start).splitlines()[-args.capture_lines :]
    payload['log_tail'] = run_log.read_text(encoding='utf-8', errors='ignore').splitlines()[-args.log_lines :] if run_log.exists() else []
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_resume(args) -> int:
    meta = load_job(args.name)
    session = meta['session']
    if not tmux_has(session):
        raise SystemExit(f'tmux session is not running: {session}')
    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).resolve().read_text(encoding='utf-8')
    assert prompt is not None
    tmux_send(session, prompt)
    append_jsonl(Path(meta['events_file']), {'ts': time.time(), 'event': 'resume_prompt_sent', 'prompt': prompt})
    print(json.dumps({'job': args.name, 'session': session, 'resumed': True}, ensure_ascii=False))
    return 0


def cmd_kill(args) -> int:
    meta = load_job(args.name)
    pid = meta.get('supervisor_pid')
    if pid:
        kill_pid(pid)
    session = meta['session']
    subprocess.run(['tmux', 'kill-session', '-t', session], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if args.remove_files:
        run_dir = Path(meta['run_dir'])
        if run_dir.exists():
            shutil.rmtree(run_dir)
        resolve_job(args.name).unlink(missing_ok=True)
    print(json.dumps({'job': args.name, 'killed': True, 'removed_files': args.remove_files}, ensure_ascii=False))
    return 0


def build_parser():
    p = argparse.ArgumentParser(description='Manage supervised Codex tmux jobs.')
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('start')
    s.add_argument('--name')
    s.add_argument('--session')
    s.add_argument('--workdir', required=True)
    group = s.add_mutually_exclusive_group(required=True)
    group.add_argument('--prompt')
    group.add_argument('--prompt-file')
    s.add_argument('--poll-seconds', type=float, default=30)
    s.add_argument('--ready-timeout', type=int)
    s.add_argument('--substantial-job', action='store_true')
    s.add_argument('--require-commit', action='store_true')
    s.add_argument('--extra-launch-args', default='')
    s.set_defaults(func=cmd_start)

    s = sub.add_parser('status')
    s.add_argument('name')
    s.set_defaults(func=cmd_status)

    s = sub.add_parser('list')
    s.add_argument('--limit', type=int, default=20)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser('tail')
    s.add_argument('name')
    s.add_argument('--lines', type=int, default=40)
    s.set_defaults(func=cmd_tail)

    s = sub.add_parser('checkin')
    s.add_argument('name')
    s.add_argument('--start', default='-120')
    s.add_argument('--capture-lines', type=int, default=40)
    s.add_argument('--log-lines', type=int, default=20)
    s.set_defaults(func=cmd_checkin)

    s = sub.add_parser('resume')
    s.add_argument('name')
    group = s.add_mutually_exclusive_group(required=True)
    group.add_argument('--prompt')
    group.add_argument('--prompt-file')
    s.set_defaults(func=cmd_resume)

    s = sub.add_parser('kill')
    s.add_argument('name')
    s.add_argument('--remove-files', action='store_true')
    s.set_defaults(func=cmd_kill)
    return p


def main() -> int:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
