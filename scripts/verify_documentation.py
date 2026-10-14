#!/usr/bin/env python3
"""Check the canonical board plus this library's RFC/index closeout contract."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--agent-skills', type=Path, required=True,
                        help='Explicit canonical AgentSkills source checkout (no personal installation required).')
    args = parser.parse_args()
    root = args.root.resolve()
    assets = args.agent_skills.resolve() / 'skills/implement-rfc'
    if not (assets / 'scripts/board_model.py').is_file():
        parser.error('--agent-skills must contain skills/implement-rfc/scripts/board_model.py; clone AgentSkills first')
    sys.path.insert(0, str(assets / 'scripts'))
    import board_model as board
    import project_config
    config = project_config.resolve_context(repo_root=root).config
    cards, errors = board.validate_board(root, config)
    problems = list(map(str, errors))
    rfc_root = root / config['rfc_root']
    index = (rfc_root / 'README.md').read_text(encoding='utf-8')
    count = 0
    for path in sorted(rfc_root.glob('RFC-*.md')):
        matter = board.parse_matter(path.read_bytes(), path)
        fields = matter.values
        rid, status = fields.get('id'), fields.get('status')
        count += 1
        if status not in {'Proposed','Accepted','Implementing','Implemented','Auto-Verified','Rejected','Superseded'}:
            problems.append('invalid RFC status ' + str(rid))
        if f'| {rid} | {status} |' not in index:
            problems.append('RFC index status mismatch ' + str(rid))
        family = [c for c in cards.values() if rid in c.rfcs]
        closeouts = [c for c in family if rid in c.fields.get('closeout_for', [])]
        if len(closeouts) != 1:
            problems.append('exactly one closeout required ' + str(rid))
            continue
        closeout = closeouts[0]
        for criterion in re.findall(r'\*\*(' + re.escape(rid) + r'-AC\d{2})\*\*', path.read_text(encoding='utf-8')):
            if f'| {criterion} |' not in closeout.body:
                problems.append('missing closeout criterion ' + criterion)
        if status == 'Auto-Verified':
            if any(c.fields['status'] != 'Done' for c in family):
                problems.append('terminal RFC has unfinished cards ' + rid)
            if not re.search(r'RFC_BASE_SHA:\s*(?:[a-f0-9]{40}|[a-f0-9]{64})\b', closeout.body):
                problems.append('terminal RFC lacks real baseline ' + rid)
            if '| Not run |' in closeout.body:
                problems.append('terminal RFC has unrun criteria ' + rid)
    for problem in problems:
        print('ERROR ' + problem, file=sys.stderr)
    print(f'{count} RFCs, {len(cards)} cards; {len(problems)} structural violations')
    return int(bool(problems))


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f'error: {error}', file=sys.stderr)
        raise SystemExit(2)
