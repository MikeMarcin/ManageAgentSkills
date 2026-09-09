#!/usr/bin/env python3
"""Validate this RFC pack, never install it or execute its setup actions."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

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
    if len(cards) != plan.get('reservation_count'):
        errors.append('reservation/card count mismatch')
    if not plan.get('provisional_ids'):
        errors.append('packet IDs must remain provisional')
    for card in cards:
        for dep in card.get('depends_on', []):
            if dep not in indexed:
                errors.append(f'missing dependency {dep}')
        if card.get('status') == 'Ready' and card.get('depends_on'):
            errors.append(f'premature Ready: {card["id"]}')
    active, done = set(), set()
    def visit(identifier):
        if identifier in active:
            errors.append(f'dependency cycle at {identifier}'); return
        if identifier in done or identifier not in indexed:
            return
        active.add(identifier)
        for dep in indexed[identifier].get('depends_on', []): visit(dep)
        active.remove(identifier); done.add(identifier)
    for key in indexed: visit(key)
    return errors

def validate_workflow(package: Path, document: dict | None = None) -> list[str]:
    doc = document if document is not None else read_json(package/'mask-workflow.json')
    errors = []
    if set(doc) - {'schema_version','inputs','native_roles','setup'} or doc.get('schema_version') != 1:
        errors.append('unsupported workflow shape/version')
    inputs = doc.get('inputs', [])
    identifiers = [v.get('id') for v in inputs]
    if len(set(identifiers)) != len(identifiers): errors.append('duplicate input')
    for item in inputs:
        if not safe_path(item.get('path')): errors.append('unsafe input path')
        if item.get('kind') not in ('text','json'): errors.append('invalid input kind')
    actions = doc.get('setup', [])
    action_ids = [a.get('id') for a in actions]
    if len(set(action_ids)) != len(action_ids): errors.append('duplicate setup action')
    for action in actions:
        if action.get('effects') != 'staged-native-roles': errors.append('unsupported setup effects')
        entry = action.get('entrypoint')
        if not safe_path(entry) or not entry.endswith('.py'):
            errors.append('unsafe/non-Python entrypoint')
        elif not (package/entry).is_file(): errors.append('missing entrypoint')
        if entry not in action.get('package_inputs', []): errors.append('entrypoint absent from package inputs')
        for name in action.get('package_inputs', []):
            if not safe_path(name) or not (package/name).is_file(): errors.append('invalid package input')
        if set(action.get('inputs', [])) - set(identifiers): errors.append('unknown consumer input')
        timeout = action.get('timeout_seconds')
        if type(timeout) is not int or not 1 <= timeout <= 120: errors.append('invalid setup timeout')
    seen = set()
    for role in doc.get('native_roles', []):
        key = (role.get('agent'), role.get('name'))
        if key in seen: errors.append('duplicate native role')
        seen.add(key)
        if key[0] not in ('codex','claude') or not isinstance(key[1],str) or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',key[1]):
            errors.append('invalid native role identity')
        if ('asset' in role) == ('setup' in role): errors.append('role must have exactly one producer')
        if 'setup' in role and role['setup'] not in action_ids: errors.append('undeclared setup action')
        if 'asset' in role:
            relative = role['asset'].get('path')
            if not safe_path(relative): errors.append('unsafe asset path'); continue
            path = package/relative
            if not path.is_file() or path.is_symlink(): errors.append('missing/nonregular role asset'); continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != role['asset'].get('sha256'): errors.append('role asset hash mismatch')
    if not seen: errors.append('no required roles')
    return errors

def validate_structure(root: Path) -> list[str]:
    errors = []
    plan = read_json(root/'issue-plan.json')
    errors += validate_plan(plan)
    rfcs = {}
    for path in sorted((root/'docs/rfcs').glob('RFC-*.md')):
        fields = matter(path)
        rid = fields['id']; rfcs[rid] = path
        if fields.get('status') != 'Proposed': errors.append(f'RFC not Proposed: {rid}')
    if len(rfcs) != 2: errors.append('expected two corrective RFCs')
    for card in plan['cards']:
        path = root/card['path']
        if not path.is_file(): errors.append(f'missing live card: {card["id"]}'); continue
        fields = matter(path)
        for field in ('id','title','status','rfcs','depends_on'):
            if fields.get(field) != card[field]: errors.append(f'card/plan mismatch: {card["id"]} {field}')
        if not fields.get('metadata', {}).get('provisional_id'): errors.append('nonprovisional issue metadata')
        if fields.get('schema') != 'implement-rfc.card.v1': errors.append('invalid card schema')
        if fields.get('closeout_for',[]) != card['closeout_for']: errors.append('closeout mismatch')
        if any(r not in rfcs for r in card['rfcs']): errors.append('unknown RFC reference')
    for rid, path in rfcs.items():
        criteria = re.findall(r'\*\*('+re.escape(rid)+r'-AC\d{2})\*\*', path.read_text())
        if len(criteria) != 8 or len(set(criteria)) != 8: errors.append(f'eight unique criteria required: {rid}')
        closeouts = [c for c in plan['cards'] if rid in c.get('closeout_for',[])]
        if len(closeouts) != 1:
            errors.append(f'exactly one closeout required: {rid}'); continue
        close = root/closeouts[0]['path']
        body = close.read_text() if close.exists() else ''
        for ac in criteria:
            if f'| {ac} |' not in body: errors.append(f'missing closeout row: {ac}')
            if not any(ac in c['criteria'] for c in plan['cards'] if not c['closeout_for']): errors.append(f'missing implementation coverage: {ac}')
    for name in ('static-package','generated-package'):
        errors += [name+': '+e for e in validate_workflow(root/'fixtures'/name)]
    inventory = read_json(root/'fixtures/legacy-inventory.json')
    rows = inventory['data']['rows']
    if len(rows) != 6 or len({r['skill'] for r in rows}) != 3: errors.append('inventory fixture not three by two')
    if any(r['host_load'] != 'not_verified' for r in rows): errors.append('invented host-load evidence')
    # Resolve actual relative Markdown links, not code block placeholders or example prose.
    for path in root.rglob('*.md'):
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if re.match(r'(?:[a-z]+:|#)', target): continue
            clean = target.split('#',1)[0]
            if clean and not (path.parent/clean).exists(): errors.append(f'broken link: {path.relative_to(root)} -> {target}')
    return errors

def validate_manifest(root: Path) -> list[str]:
    errors = []
    manifest = read_json(root/'PACK_MANIFEST.json')
    listed = {row['path']:row for row in manifest['files']}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name != 'PACK_MANIFEST.json'}
    if len(listed) != len(manifest['files']): errors.append('duplicate manifest path')
    if set(listed) != actual: errors.append('manifest file set mismatch')
    for name, row in listed.items():
        if not safe_path(name): errors.append('unsafe manifest path'); continue
        path = root/name
        if not path.is_file() or path.is_symlink(): errors.append('missing/nonregular manifest file'); continue
        data = path.read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            errors.append('manifest hash mismatch: '+name)
    return errors

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--jsonschema',action='store_true',help='Also use separately installed jsonschema to check the proposed schema/examples')
    args = parser.parse_args(argv); root=args.root.resolve()
    errors = validate_structure(root) + validate_manifest(root)
    if args.jsonschema:
        import jsonschema
        schema = read_json(root/'contracts/workflow-requirements.v1.schema.json')
        jsonschema.Draft202012Validator.check_schema(schema)
        for name in ('static-package','generated-package'):
            jsonschema.validate(read_json(root/'fixtures'/name/'mask-workflow.json'),schema)
    for error in errors: print('ERROR '+error,file=sys.stderr)
    print(f'2 proposed RFCs; 12 provisional cards; 16 criteria; {len(errors)} pack violations.')
    print('Pack integrity only: not MASK implementation, native qualification, or host-loading evidence.')
    return int(bool(errors))

if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('Pack validation failed: '+str(error),file=sys.stderr); raise SystemExit(2)
