#!/usr/bin/env python3
"""Validate this RFC pack; never install it, migrate a machine or run MASK."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RFC_COUNT = 1
CARD_COUNT = 9
CRITERIA_PER_RFC = 8


def read_json(path: Path):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f'Duplicate key: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def matter(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError(f'Missing frontmatter: {path}')
    header = text[4:].split('\n---\n', 1)[0]
    return {key: json.loads(value.strip()) for key, value in
            (line.split(':', 1) for line in header.splitlines())}


def safe_path(value) -> bool:
    return (isinstance(value, str) and bool(value) and len(value.encode('utf-8')) <= 1024
            and '\\' not in value and ':' not in value
            and not value.startswith('/') and all(ord(c) >= 32 for c in value)
            and all(part not in ('', '.', '..') for part in value.split('/')))


def validate_plan(plan: dict) -> list[str]:
    errors = []
    cards = plan.get('cards', [])
    indexed = {c.get('id'): c for c in cards}
    if len(indexed) != len(cards):
        errors.append('duplicate card ID')
    if len(cards) != plan.get('reservation_count') or len(cards) != CARD_COUNT:
        errors.append('reservation/card count mismatch')
    if not plan.get('provisional_ids'):
        errors.append('packet IDs must remain provisional')
    for card in cards:
        for dep in card.get('depends_on', []):
            if dep not in indexed:
                errors.append(f'missing dependency {dep}')
        if card.get('status') == 'Ready' and card.get('depends_on'):
            errors.append(f'premature Ready: {card["id"]}')
    if sum(card.get('status') == 'Ready' for card in cards) != 1:
        errors.append('exactly one Ready intake card expected')
    active, done = set(), set()

    def visit(identifier):
        if identifier in active:
            errors.append(f'dependency cycle at {identifier}')
            return
        if identifier in done or identifier not in indexed:
            return
        active.add(identifier)
        for dep in indexed[identifier].get('depends_on', []):
            visit(dep)
        active.remove(identifier)
        done.add(identifier)
    for key in indexed:
        visit(key)
    return errors


def validate_milestones(root: Path, plan: dict) -> list[str]:
    errors = []
    milestones = read_json(root / 'milestone-plan.json')
    if milestones.get('schema') != 'implement-rfc.milestone-plan.v1':
        errors.append('unsupported milestone plan schema')
    issues = set(milestones.get('scope', {}).get('issues', []))
    planned = {card['id'] for card in plan['cards']}
    if issues != planned:
        errors.append('milestone scope issues differ from the card plan')
    seen, ids = set(), set()
    for milestone in milestones.get('milestones', []):
        if milestone.get('id') in ids:
            errors.append('duplicate milestone id')
        ids.add(milestone.get('id'))
        for work in milestone.get('work', []):
            identifier = work.get('issue') or work.get('rfc')
            if identifier in seen:
                errors.append(f'work listed twice: {identifier}')
            seen.add(identifier)
            if work.get('issue') and work['issue'] not in planned:
                errors.append(f'milestone work outside the card plan: {work["issue"]}')
        if not milestone.get('exit_criteria'):
            errors.append(f'milestone without exits: {milestone.get("id")}')
    for milestone in milestones.get('milestones', []):
        for dep in milestone.get('depends_on', []):
            if dep not in ids:
                errors.append(f'unknown milestone prerequisite {dep}')
    if seen != planned:
        errors.append('every card must appear in exactly one milestone')
    return errors


def validate_structure(root: Path) -> list[str]:
    errors = []
    plan = read_json(root / 'issue-plan.json')
    errors += validate_plan(plan)
    rfcs = {}
    for path in sorted((root / 'docs/rfcs').glob('RFC-*.md')):
        fields = matter(path)
        rid = fields['id']
        rfcs[rid] = path
        if fields.get('status') != 'Proposed':
            errors.append(f'RFC not Proposed: {rid}')
        if not path.name.startswith(rid + '-'):
            errors.append(f'RFC filename does not start with its id: {path.name}')
    if len(rfcs) != RFC_COUNT:
        errors.append('expected one corrective RFC')
    for card in plan['cards']:
        path = root / card['path']
        if not path.is_file():
            errors.append(f'missing live card: {card["id"]}')
            continue
        if not path.name.startswith(card['id'] + '-'):
            errors.append(f'card filename does not start with its id: {path.name}')
        fields = matter(path)
        for field in ('id', 'title', 'status', 'rfcs', 'depends_on'):
            if fields.get(field) != card[field]:
                errors.append(f'card/plan mismatch: {card["id"]} {field}')
        if not fields.get('metadata', {}).get('provisional_id'):
            errors.append('nonprovisional issue metadata')
        if fields.get('schema') != 'implement-rfc.card.v1':
            errors.append('invalid card schema')
        if fields.get('closeout_for', []) != card['closeout_for']:
            errors.append('closeout mismatch')
        if any(r not in rfcs for r in card['rfcs']):
            errors.append('unknown RFC reference')
        lane = path.parent.name
        expected_status = {'20-ready': 'Ready', '10-backlog': 'Backlog'}.get(lane)
        if fields.get('status') != expected_status:
            errors.append(f'lane/status mismatch: {card["id"]}')
        body = path.read_text(encoding='utf-8')
        coverage = re.search(r'^Criterion coverage: (.+)\.$', body, re.M)
        listed = [item.strip() for item in coverage.group(1).split(',')] if coverage else []
        if listed != card['criteria']:
            errors.append(f'criterion coverage line differs from plan: {card["id"]}')
    for rid, path in rfcs.items():
        criteria = re.findall(r'\*\*(' + re.escape(rid) + r'-AC\d{2})\*\*', path.read_text(encoding='utf-8'))
        if len(criteria) != CRITERIA_PER_RFC or len(set(criteria)) != CRITERIA_PER_RFC:
            errors.append(f'eight unique criteria required: {rid}')
        closeouts = [c for c in plan['cards'] if rid in c.get('closeout_for', [])]
        if len(closeouts) != 1:
            errors.append(f'exactly one closeout required: {rid}')
            continue
        close = root / closeouts[0]['path']
        body = close.read_text(encoding='utf-8') if close.exists() else ''
        if 'RFC_BASE_SHA: Not recorded' not in body:
            errors.append('closeout must not carry a claimed baseline')
        if re.search(r'\| (?:pass|PASS) \|', body):
            errors.append('closeout must not claim a PASS')
        for ac in criteria:
            if f'| {ac} |' not in body:
                errors.append(f'missing closeout row: {ac}')
            if not any(ac in c['criteria'] for c in plan['cards'] if not c['closeout_for']):
                errors.append(f'missing implementation coverage: {ac}')
    schema = read_json(root / 'contracts/machine-v3.schema.json')
    if schema.get('properties', {}).get('schema_version', {}).get('const') != 3 or 'source' in schema.get('properties', {}):
        errors.append('machine v3 schema must be version 3 without a live source block')
    errors += validate_milestones(root, plan)
    for path in root.rglob('*.md'):
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if re.match(r'(?:[a-z]+:|#)', target):
                continue
            clean = target.split('#', 1)[0]
            if clean and not (path.parent / clean).exists():
                errors.append(f'broken link: {path.relative_to(root)} -> {target}')
    return errors


def validate_manifest(root: Path) -> list[str]:
    errors = []
    manifest = read_json(root / 'PACK_MANIFEST.json')
    if manifest.get('milestone_plan') != 'milestone-plan.json':
        errors.append('manifest must point at milestone-plan.json')
    if manifest.get('rfcs') != ['RFC-MASK-0020'] or manifest.get('status') != 'proposed':
        errors.append('manifest must name the single proposed RFC')
    listed = {row['path']: row for row in manifest['files']}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and p.name != 'PACK_MANIFEST.json' and '__pycache__' not in p.parts}
    if len(listed) != len(manifest['files']):
        errors.append('duplicate manifest path')
    if set(listed) != actual:
        errors.append('manifest file set mismatch: ' + ', '.join(sorted(set(listed) ^ actual)))
    if manifest.get('file_count') != len(listed):
        errors.append('manifest file_count mismatch')
    for name, row in listed.items():
        if not safe_path(name):
            errors.append('unsafe manifest path')
            continue
        path = root / name
        if not path.is_file() or path.is_symlink():
            errors.append('missing/nonregular manifest file')
            continue
        data = path.read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            errors.append('manifest hash mismatch: ' + name)
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--skip-manifest', action='store_true', help='Structure only; used before the manifest is generated')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = validate_structure(root)
    if not args.skip_manifest:
        errors += validate_manifest(root)
    for error in errors:
        print('ERROR ' + error, file=sys.stderr)
    print(f'{RFC_COUNT} proposed RFC; {CARD_COUNT} provisional cards; {CRITERIA_PER_RFC} criteria; {len(errors)} pack violations.')
    print('Pack integrity only: not MASK implementation, native qualification or a migrated machine.')
    return int(bool(errors))


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Pack validation failed: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
