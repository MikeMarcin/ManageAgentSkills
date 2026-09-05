#!/usr/bin/env python3
"""Allocate local issue IDs on main. Repository support, not a MASK command."""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path

def atomic_write(path: Path, value: str) -> None:
    if path.is_symlink(): raise ValueError(f"refusing symlink: {path}")
    fd, tmp = tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
            out.write(value); out.flush(); os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path.cwd())
    ap.add_argument('--count',type=int,default=1)
    ap.add_argument('--reserve-for')
    ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args(); root=a.root.resolve()
    if not 1 <= a.count <= 1000: raise ValueError('count must be 1..1000')
    if a.reserve_for and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',a.reserve_for):
        raise ValueError('reserve-for must be a lower-case hyphenated token')
    branch=subprocess.run(['git','-C',str(root),'branch','--show-current'],capture_output=True,text=True,timeout=10)
    if branch.returncode or branch.stdout.strip()!='main': raise ValueError('allocation belongs to the integrator on main')
    cfg_path=root/'.mask/skill-config/implement-rfc/project.json'
    cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    counter=(root/cfg['next_id']['path']).resolve()
    reservation=(root/cfg['reservations_dir']).resolve()
    if not counter.is_relative_to(root) or not reservation.is_relative_to(root): raise ValueError('tracker path escapes root')
    lock=counter.parent/'_allocator.lock'; lockfd=None
    try:
        if not a.dry_run:
            lockfd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.write(lockfd,str(os.getpid()).encode())
        old=counter.read_text(encoding='utf-8').strip()
        match=re.fullmatch(r'([A-Z]{2,8})-(\d{4})',old)
        if not match: raise ValueError('NEXT_ID must be PREFIX-NNNN')
        prefix,start=match.group(1),int(match.group(2)); end=start+a.count-1
        if end>=9999: raise ValueError('four-digit ID space exhausted')
        ids=[f'{prefix}-{n:04d}' for n in range(start,end+1)]
        used={p.name.split('-',2)[0]+'-'+p.name.split('-',2)[1] for p in (root/cfg['issue_root']).glob('*/*.md') if re.match(r'^[A-Z]{2,8}-\d{4}-',p.name)}
        if any(i in used for i in ids): raise ValueError('NEXT_ID collides with live cards; reconcile the board')
        receipt=reservation/f'{ids[0]}--{ids[-1]}--{a.reserve_for}.json' if a.reserve_for else None
        if receipt and receipt.exists(): raise ValueError('reservation receipt already exists')
        if not a.dry_run:
            atomic_write(counter,f'{prefix}-{end+1:04d}\n')
            if receipt:
                reservation.mkdir(parents=True,exist_ok=True)
                with receipt.open('x',encoding='utf-8',newline='\n') as out:
                    json.dump({'schema_version':1,'lane':a.reserve_for,'ids':ids},out,indent=2);out.write('\n')
        print(json.dumps({'ids':ids,'next_id':f'{prefix}-{end+1:04d}','dry_run':a.dry_run,'reservation':str(receipt) if receipt else None}))
        return 0
    finally:
        if lockfd is not None:
            os.close(lockfd);lock.unlink()

if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:
        print(f'error: {e}',file=sys.stderr);raise SystemExit(2)
