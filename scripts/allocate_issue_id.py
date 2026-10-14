#!/usr/bin/env python3
"""Repository entrypoint for the canonical board allocator."""
import argparse
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--count',type=int,default=1)
p.add_argument('--reserve-for',required=True)
p.add_argument('--dry-run',action='store_true')
p.add_argument('--agent-skills',type=Path,help='Canonical AgentSkills source checkout; otherwise use the explicitly installed workflow')
a=p.parse_args()
script=(a.agent_skills / 'skills/implement-rfc' if a.agent_skills else a.root / '.agents/skills/implement-rfc') / 'scripts/issue_board.py'
if not script.is_file():
    p.error('Clone AgentSkills and pass --agent-skills PATH, or install implement-rfc before allocating')
command=[sys.executable,str(script),'--repo-root',str(a.root.resolve()),'allocate','--count',str(a.count),'--reserve-for',a.reserve_for,'--json']
if a.dry_run:command.append('--dry-run')
sys.exit(subprocess.call(command))
