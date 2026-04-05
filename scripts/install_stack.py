#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def load_manifest(repo_root: Path) -> dict[str, str]:
    payload = json.loads((repo_root / 'skills' / 'install-manifest.json').read_text(encoding='utf-8'))
    return {name: meta['tier'] for name, meta in payload['skills'].items()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Install the core agent tmux coding skill stack into a Hermes-style skill directory. Optional OMX support must be enabled explicitly.'
    )
    parser.add_argument('--dest', required=True, help='Destination skills directory, e.g. $HOME/.hermes/skills')
    parser.add_argument(
        '--include-skill',
        action='append',
        default=[],
        help='Optional skill to install in addition to the core set. May be repeated.',
    )
    parser.add_argument(
        '--include-omx',
        action='store_true',
        help='Compatibility alias for --include-skill oh-my-codex.',
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    tiers = load_manifest(repo_root)
    src = repo_root / 'skills' / 'autonomous-ai-agents'
    dest = Path(args.dest).resolve() / 'autonomous-ai-agents'
    dest.mkdir(parents=True, exist_ok=True)

    requested_optional = set(args.include_skill)
    if args.include_omx:
        requested_optional.add('oh-my-codex')
    unknown = sorted(requested_optional - set(tiers))
    if unknown:
        raise SystemExit(f'unknown skill(s): {", ".join(unknown)}')

    copied = []
    skipped_optional = []
    for item in sorted(src.iterdir()):
        target = dest / item.name
        if item.is_dir():
            tier = tiers.get(item.name)
            if tier is None:
                raise SystemExit(f'skill missing from manifest: {item.name}')
            if tier == 'optional' and item.name not in requested_optional:
                skipped_optional.append(item.name)
                continue
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copy2(item, target)
        copied.append(str(target))

    print('Installed skill stack to:', dest)
    for path in copied:
        print('-', path)
    for skill in skipped_optional:
        print(f'Skipped optional skill: {skill} (use --include-skill {skill} to install it)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
