#!/usr/bin/env python3
"""Exercise old public MASK behavior in disposable roots. Never modifies real consumers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PACK = Path(__file__).resolve().parents[1]

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--program',type=Path,required=True,help='Explicit mask.py source snapshot to execute')
    parser.add_argument('--out',type=Path,help='Optional new JSON report path; existing output is refused')
    args=parser.parse_args(); program=args.program.resolve()
    if not program.is_file(): parser.error('mask.py not found')
    if args.out and (args.out.exists() or args.out.is_symlink()): parser.error('Output already exists')
    with tempfile.TemporaryDirectory(prefix='mask-corrective-baseline-') as temporary:
        base=Path(temporary); source=base/'AgentSkills'; project=base/'SampleReview'; home=base/'machine'
        source.mkdir(); project.mkdir()
        env=dict(os.environ,MASK_HOME=str(home),PYTHONDONTWRITEBYTECODE='1',GIT_TERMINAL_PROMPT='0')
        def git(root,*values):
            subprocess.run(['git','-C',str(root),*values],check=True,capture_output=True,env=env,timeout=20)
        for root in (source,project):
            git(root,'init','-b','main');git(root,'config','user.name','Disposable Fixture');git(root,'config','user.email','fixture@example.invalid')
        (source/'skills').mkdir()
        shutil.copytree(PACK/'fixtures/static-package',source/'skills/implement-rfc')
        for name in ('attended-review','wizard'):
            root=source/'skills'/name;root.mkdir()
            (root/'SKILL.md').write_text(f'---\nname: {name}\ndescription: Synthetic baseline fixture\n---\n\nFixture only.\n')
        shutil.copytree(PACK/'fixtures/consumer/.mask',project/'.mask')
        git(source,'add','skills');git(source,'commit','-m','Synthetic baseline source')
        records=[]
        def invoke(values,machine=True):
            argv=[sys.executable,'-B',str(program),*map(str,values)]
            if machine:argv.append('--json')
            run=subprocess.run(argv,capture_output=True,encoding='utf-8',cwd=project,env=env,timeout=40)
            try:payload=json.loads(run.stdout)
            except json.JSONDecodeError:payload=None
            record={'argv':['mask',*[str(v).replace(str(base),'/fixture') for v in values],*(['--json'] if machine else [])],
                    'exit_code':run.returncode,'stdout_is_json':payload is not None}
            if isinstance(payload,dict):
                record.update(ok=payload.get('ok'),readiness=payload.get('data',{}).get('readiness'),error=(payload.get('error') or {}).get('code'))
            records.append(record)
            if run.returncode: raise RuntimeError('Baseline setup failed: '+json.dumps(record))
            return payload
        invoke(['init','--source',source])
        invoke(['project','init','--project',project])
        invoke(['project','register','--project',project])
        invoke(['project','require','attended-review','implement-rfc','wizard','--project',project,'--apply'])
        invoke(['integration','approve','--project',project])
        ensure=invoke(['ensure','--project',project])
        check=invoke(['ensure','--project',project,'--check'])
        inventory=invoke(['inventory','--project',project],machine=False)
        missing=[]
        for agent,suffix in [('codex','toml'),('claude','md')]:
            relative=f'.{agent}/agents/rfc-integrator.{suffix}'
            if not (project/relative).exists(): missing.append(relative)
        result={'schema':'mask.corrective-pack.baseline.v1','basis':'synthetic public-CLI reproduction against explicit supplied snapshot',
                'program_sha256':hashlib.sha256(program.read_bytes()).hexdigest(),
                'python':sys.version.split()[0],'platform':sys.platform,
                'observations':{'inventory_without_json_flag_parsed_as_json':isinstance(inventory,dict),
                                'inventory_link_rows':len((inventory or {}).get('data',{}).get('rows',[])),
                                'ensure_succeeded':ensure.get('ok'),
                                'ensure_check_succeeded':check.get('ok'),
                                'required_role_outputs_absent':missing,
                                'package_setup_executed':False},'commands':records,
                'limits':['Synthetic source package, not a live SRV remeasurement.',
                          'Proposed workflow descriptor is passive/unknown to the original snapshot; original ensure validates links, not these declared role requirements.',
                          'This shows the old boundary and does not qualify the new implementation or native hosts.',
                          'No provider/model/network call or real consumer/configuration change. Temporary roots were removed.']}
    text=json.dumps(result,indent=2)+'\n'
    if args.out:
        with args.out.open('x',encoding='utf-8') as stream:stream.write(text)
    print(text,end='');return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)
