#!/usr/bin/env python3
"""Validate this RFC packet, not the proposed MASK runtime."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

def load(path):
    def pairs(items):
        out={}
        for key,val in items:
            if key in out: raise ValueError(f'duplicate JSON key: {key}')
            out[key]=val
        return out
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def digest(value):
    return 'sha256:'+hashlib.sha256(value if isinstance(value,bytes) else canonical(value)).hexdigest()

def matter(path):
    text=path.read_text(encoding='utf-8')
    if not text.startswith('---\n'): raise ValueError(f'missing frontmatter: {path}')
    head,body=text[4:].split('\n---\n',1)
    result={}
    for line in head.splitlines():
        key,val=line.split(': ',1)
        if key in result: raise ValueError(f'duplicate frontmatter key: {path}: {key}')
        result[key]=json.loads(val)
    return result,body

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--jsonschema',action='store_true',help='Also validate proposed examples with the optional installed jsonschema library.')
    args=ap.parse_args();root=args.root.resolve();idx=load(root/'packet-index.json');errors=[]
    def check(cond,msg):
        if not cond:errors.append(msg)
    cards={c['id']:c for c in idx['cards']};rfcs={r['id']:r for r in idx['rfcs']}
    allids=list(cards)+[t['id'] for t in idx['tracking_items']]
    check(len(allids)==len(set(allids)),'duplicate card ID')
    check(len(rfcs)==len(idx['rfcs']),'duplicate RFC ID')
    check(idx['reservation_count']==len(allids),'reservation count mismatch')
    check(not list(root.glob('**/NEXT_ID')),'packet must not overwrite live counter')
    check(not list(root.glob('**/.git')),'packet must not carry an executable/source Git checkout')
    for rid,r in rfcs.items():
        p=root/r['path'];check(p.is_file(),f'missing RFC {rid}')
        front,body=matter(p);check(front['id']==rid,f'RFC frontmatter ID {rid}')
        check(front['status']=='Proposed',f'RFC falsely terminal: {rid}')
        expected={f'{rid}-AC{i:02d}' for i in range(1,len(r['criteria'])+1)}
        actual=set(re.findall(r'\*\*('+re.escape(rid)+r'-AC\d{2})\*\*',body))
        check(actual==expected,f'criterion inventory mismatch: {rid}')
        family=[c for c in cards.values() if c['rn']==r['n']]
        close=[c for c in family if c.get('closeout')]
        check(len(close)==1,f'closeout count: {rid}')
        if close:
            cf,cb=matter(root/close[0]['path'])
            check(cf.get('closeout_for')==[rid],f'closeout link mismatch: {rid}')
            for ac in expected:check(f'| {ac} |' in cb,f'missing closeout row: {ac}')
            check('RFC_BASE_SHA: UNRECORDED' in cb,f'fabricated baseline: {rid}')
        covered={a for c in family if not c.get('closeout') for a in c['ac']}
        check(covered==set(range(1,len(r['criteria'])+1)),f'implementation coverage missing: {rid}')
    for cid,c in cards.items():
        front,body=matter(root/c['path'])
        check(front['id']==cid,f'card ID mismatch: {cid}')
        check(front['schema']=='implement-rfc.card.v1',f'card schema: {cid}')
        check(front['status']=='Backlog',f'unexpected work status: {cid}')
        check(front['depends_on']==c['depends_on'],f'dependency mismatch: {cid}')
        for dep in c['depends_on']:check(dep in cards,f'missing local dependency {cid}->{dep}')
    for t in idx['tracking_items']:
        f,b=matter(root/t['path']);check(f['status']=='Inbox' and f['rfcs']==[],f'tracking scope/status: {t["id"]}')
    visiting=set();done=set()
    def visit(cid):
        if cid in done:return
        if cid in visiting:raise ValueError('dependency cycle at '+cid)
        visiting.add(cid)
        for dep in cards[cid]['depends_on']:visit(dep)
        visiting.remove(cid);done.add(cid)
    for cid in cards:visit(cid)
    # All local Markdown links must resolve. External URIs and fragment-only links are not fetched.
    for path in root.rglob('*.md'):
        text=path.read_text(encoding='utf-8')
        for dest in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)',text):
            if '://' in dest or dest.startswith(('#','mailto:')):continue
            dest=dest.split('#',1)[0]
            if dest:check((path.parent/dest).resolve().exists(),f'broken local link: {path.relative_to(root)} -> {dest}')
    for path in root.rglob('*.json'):load(path)
    payload_digests={}
    for sid in ('alpha','mac-notes'):
        base=root/'examples/fixture-source/skills'/sid;manifest=[]
        for path in sorted(base.rglob('*')):
            if path.is_file():
                data=path.read_bytes();manifest.append(dict(path=path.relative_to(base).as_posix(),mode='100644',size=len(data),sha256=digest(data)))
        check(manifest==load(root/f'examples/payload-manifest-{sid}.json'),f'payload manifest mismatch: {sid}')
        payload_digests[sid]=digest(manifest)
    pairs=[('examples/project/.mask.json','examples/project/.mask.lock.json'),('examples/personal/selection.json','examples/personal/selection.lock.json')]
    for sp,lp in pairs:
        sel,lock=load(root/sp),load(root/lp)
        check(lock['selection_digest']==digest(sel),f'selection digest mismatch: {sp}')
        check({(s['source'],s['id']) for s in sel['skills']}=={(s['source'],s['id']) for s in lock['packages']},f'lock membership mismatch: {lp}')
        for p in lock['packages']:
            check(p['payload_digest']==payload_digests[p['id']],f'payload digest: {lp}')
            check(p['commit']==idx['fixture_commit'],f'fixture commit mismatch: {lp}')
            check(p['metadata_digest']==digest(load(root/f'examples/fixture-source/skills/{p["id"]}/mask-skill.json')),f'metadata digest: {lp}')
    report=load(root/'examples/fleet-report.json')
    check(report['data']['example_only'] and not report['ok'] and not report['data']['complete'] and not report['data']['installed_everywhere'],'example false completion')
    check(report['error']['code']=='fleet.incomplete','example wrong incomplete error')
    html=(root/'examples/fleet-report.html').read_text()
    check('ILLUSTRATIVE ONLY' in html,'HTML needs example banner')
    check('<script' not in html.lower() and 'src="http' not in html.lower(),'HTML has executable/remote dependency')
    schema_count=0
    if args.jsonschema:
        try:from jsonschema import Draft202012Validator
        except ImportError:raise ValueError('jsonschema not installed; run base packet check without --jsonschema, or install the optional validation dependency explicitly.')
        schemas={}
        for p in (root/'contracts').glob('*.schema.json'):
            s=load(p);Draft202012Validator.check_schema(s);schemas[p.name]=Draft202012Validator(s);schema_count+=1
        for sp,lp in pairs:
            schemas['selection-v2.schema.json'].validate(load(root/sp));schemas['lock-v1.schema.json'].validate(load(root/lp))
        for sid in ('alpha','mac-notes'):schemas['skill-metadata-v1.schema.json'].validate(load(root/f'examples/fixture-source/skills/{sid}/mask-skill.json'))
        schemas['source-index-v1.schema.json'].validate(load(root/'examples/fixture-source/mask-source.json'))
    if errors:
        for e in errors:print('ERROR:',e,file=sys.stderr)
        return 1
    print(f'PASS: {len(rfcs)} proposed RFCs; {len(cards)} implementation/closeout cards; {len(idx["tracking_items"])} deferred items; one closeout each; acyclic dependencies; full acceptance coverage; local links; JSON and fixture digests.')
    if schema_count:print(f'PASS: {schema_count} proposed JSON Schemas and seven associated fixture documents.')
    print('Boundary: packet structure/contracts only. No MASK runtime, native host or real-device acceptance was performed.')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR:',exc,file=sys.stderr);raise SystemExit(2)
