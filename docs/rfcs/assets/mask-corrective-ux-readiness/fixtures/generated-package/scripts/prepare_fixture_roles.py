#!/usr/bin/env python3
"""Synthetic staged-role fixture. Do not use as a production AgentSkills generator."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--request-file', type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request_file.read_text(encoding='utf-8'))
    if request.get('schema') != 'mask.setup-request.v1' or request.get('action') != 'prepare-roles':
        parser.error('Unsupported fixture request')
    if not args.repo_root.is_dir() or not args.output_root.is_dir():
        parser.error('Both roots must already exist')
    for role in request.get('native_roles', []):
        agent, name = role.get('agent'), role.get('name')
        if agent not in ('codex', 'claude') or not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            parser.error('Invalid fixture role')
        suffix = 'toml' if agent == 'codex' else 'md'
        destination = args.output_root / agent / (name + '.' + suffix)
        destination.parent.mkdir(exist_ok=True)
        if destination.parent.is_symlink():
            parser.error('Linked stage parent refused')
        text = (f'name = "{name}"\nmodel = "fixture-model-do-not-run"\n' if agent == 'codex'
                else f'---\nname: {name}\nmodel: fixture-model-do-not-run\n---\nFixture only.\n')
        # Exclusive creation deliberately refuses retries into an occupied stage.
        with destination.open('x', encoding='utf-8') as stream:
            stream.write(text)
    print('Fixture stage written; MASK must validate before any publication.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
