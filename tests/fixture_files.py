"""Small file helpers shared by fixtures: MASK's on-disk JSON form, and a snapshot of a tree that never follows links."""
import json
import os
from pathlib import Path
import subprocess


def text_json(value):
    """MASK's on-disk JSON form (``mask_core.text_json``)."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=True).stdout.strip()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text_json(value))


def snapshot(base, *roots, ignore=('.git', 'operation.lock')):
    """Files and links (not directories) under ``roots``, keyed relative to ``base``; links are never followed."""
    observed = {}
    for root in roots:
        for parent, directories, files in os.walk(root, followlinks=False):
            directories[:] = [name for name in directories if name not in ignore]
            for name in directories + files:
                path = Path(parent) / name
                if name in ignore:
                    continue
                key = path.relative_to(base).as_posix()
                if path.is_symlink():
                    observed[key] = ('link', os.readlink(path))
                elif path.is_file():
                    observed[key] = ('file', path.read_bytes())
    return observed
