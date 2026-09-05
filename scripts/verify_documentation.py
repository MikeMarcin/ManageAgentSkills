#!/usr/bin/env python3
"""Verify this project's live RFC/card structure; retained assets are not live."""
from __future__ import annotations
import argparse,json,re,sys,subprocess
from pathlib import Path

def fields(path):
    body=path.read_text(encoding='utf-8')
    if not body.startswith('---\n'): raise ValueError(f'{path}: missing frontmatter')
    end=body.find('\n---',4)
    if end<0: raise ValueError(f'{path}: unclosed frontmatter')
    pairs={}
    for line in body[4:end].splitlines():
        if ':' in line:
            k,v=line.split(':',1)
            if k in pairs: raise ValueError(f'{path}: duplicate field {k}')
            pairs[k]=v.strip().strip('"')
    return pairs,body

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path.cwd());a=ap.parse_args()
    root=a.root.resolve(); cfg=json.loads((root/'.mask/skill-config/implement-rfc/project.json').read_text())
    issue=root/cfg['issue_root'];rfcroot=root/cfg['rfc_root']; problems=[];cards={};rfcs={}
    for path in sorted(rfcroot.glob('RFC-*.md')):
        f,b=fields(path); rid=f.get('id','')
        if rid in rfcs: problems.append('duplicate RFC '+rid)
        if not path.name.startswith(rid+'-'): problems.append('RFC filename mismatch '+str(path))
        rfcs[rid]=(f,b,path)
    for lane,status in cfg['lane_statuses'].items():
        for path in sorted((issue/lane).glob('*.md')):
            f,b=fields(path);cid=f.get('id','')
            if not re.fullmatch(r'[A-Z]{2,8}-\d{4}',cid): problems.append('invalid card id '+str(path))
            if cid in cards: problems.append('duplicate card '+cid)
            if not path.name.startswith(cid+'-'): problems.append('card filename mismatch '+str(path))
            if f.get('status')!=status: problems.append('lane/status mismatch '+str(path))
            if f.get('rfc') not in rfcs: problems.append('missing live RFC for '+cid)
            try: deps=json.loads(f.get('depends_on','[]'))
            except json.JSONDecodeError: deps=[];problems.append('invalid dependency array '+cid)
            cards[cid]=(f,b,path,deps)
    for cid,(f,b,p,deps) in cards.items():
        for d in deps:
            if d not in cards: problems.append(f'{cid}: missing local dependency {d}')
    visiting=set();done=set()
    def visit(cid):
        if cid in visiting: problems.append('dependency cycle '+cid);return
        if cid in done or cid not in cards:return
        visiting.add(cid)
        for d in cards[cid][3]:visit(d)
        visiting.remove(cid);done.add(cid)
    for cid in cards:visit(cid)
    nxt=(root/cfg['next_id']['path']).read_text().strip();m=re.fullmatch(r'([A-Z]{2,8})-(\d{4})',nxt)
    if not m:problems.append('invalid NEXT_ID')
    else:
        high=max([int(i.rsplit('-',1)[1]) for i in cards if i.startswith(m.group(1)+'-')]+[0])
        if int(m.group(2))<=high:problems.append('NEXT_ID is not above live cards')
        for rp in (root/cfg['reservations_dir']).glob('*.json'):
            reservation=json.loads(rp.read_text())
            for token in reservation.get('ids',[]):
                if re.fullmatch(re.escape(m.group(1))+r'-\d{4}',token) and int(token.rsplit('-',1)[1])>=int(m.group(2)):
                    problems.append('NEXT_ID does not cover reservation '+token)
        history=subprocess.run(['git','-C',str(root),'log','-p','--format=','--',cfg['next_id']['path']],capture_output=True,text=True,timeout=10)
        if history.returncode==0:
            oldvals=[int(v) for v in re.findall(r'^\+'+re.escape(m.group(1))+r'-(\d{4})\s*$',history.stdout,re.MULTILINE)]
            if oldvals and max(oldvals)>int(m.group(2)):problems.append('NEXT_ID rewinds committed history')

    index=(rfcroot/'README.md').read_text(encoding='utf-8')
    for rid,(f,b,p) in rfcs.items():
        status=f.get('status')
        if status not in {'Proposed','Accepted','Implementing','Auto-Verified','Rejected','Superseded'}:problems.append('invalid RFC status '+rid)
        if f'| {rid} | {status} |' not in index:problems.append('RFC index status mismatch '+rid)
        family=[v for v in cards.values() if v[0].get('rfc')==rid]
        close=[v for v in family if v[0].get('closeout','').lower()=='true']
        if len(close)!=1:problems.append('exactly one closeout required '+rid);continue
        criteria=re.findall(r'\*\*('+re.escape(rid)+r'-AC\d{2})\*\*',b)
        for ac in criteria:
            if f'| {ac} |' not in close[0][1]:problems.append('missing closeout criterion '+ac)
        if status=='Auto-Verified':
            if any(v[0].get('status')!='Done' for v in family):problems.append('terminal RFC has unfinished cards '+rid)
            if not re.search(r'RFC_BASE_SHA:\s*(?:[a-f0-9]{40}|[a-f0-9]{64})\b',close[0][1]):problems.append('terminal RFC lacks real baseline '+rid)
            if '| Not run |' in close[0][1]:problems.append('terminal RFC has unrun criteria '+rid)
    for p in problems:print('ERROR '+p,file=sys.stderr)
    print(f'{len(rfcs)} RFCs, {len(cards)} cards; {len(problems)} structural violations')
    return 1 if problems else 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError) as e:
        print(f'error: {e}',file=sys.stderr);raise SystemExit(2)
