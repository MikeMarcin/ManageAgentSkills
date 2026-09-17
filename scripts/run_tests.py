#!/usr/bin/env python3
"""Run the unittest suite in parallel: one process per TestCase class, standard library only.

    python3 -B scripts/run_tests.py            # everything, one worker per CPU
    python3 -B scripts/run_tests.py -k update  # classes whose id contains "update"
    python3 -B scripts/run_tests.py -j 1       # serial

Each class runs as its own ``python -B -m unittest`` process, so tests that patch the process environment,
rebind a module function or crash on purpose stay isolated exactly as under ``python -m unittest MODULE``.
Output is shown only for a class that fails.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def classes(suite, found):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            classes(item, found)
        else:
            found.setdefault(f'{type(item).__module__}.{type(item).__qualname__}', 0)
            found[f'{type(item).__module__}.{type(item).__qualname__}'] += 1
    return found


def run(name):
    start = time.monotonic()
    done = subprocess.run([sys.executable, '-B', '-m', 'unittest', name], cwd=ROOT, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    ran = re.search(r'^Ran (\d+) test', done.stdout, re.MULTILINE)
    skipped = re.search(r'skipped=(\d+)', done.stdout)
    return name, done.returncode, done.stdout, time.monotonic() - start, int(ran.group(1)) if ran else 0, int(skipped.group(1)) if skipped else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('-j', '--jobs', type=int, default=os.cpu_count() or 4, help='parallel processes (default: CPU count)')
    parser.add_argument('-k', dest='pattern', action='append', default=[], help='only classes whose dotted id contains this text; repeatable')
    parser.add_argument('--slowest', type=int, default=0, metavar='N', help='also list the N slowest classes')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    found = classes(unittest.TestLoader().discover(str(ROOT / 'tests'), top_level_dir=str(ROOT)), {})
    broken = [name for name in found if name.startswith('unittest.loader.')]
    if broken:
        print('A test module failed to import; run python3 -m unittest discover -s tests -t . to see it.')
        return 1
    names = sorted(name for name in found if not args.pattern or any(text in name for text in args.pattern))
    if not names:
        print('No test classes match.')
        return 1
    # Largest classes first, so the long ones do not start last and set the wall time.
    names.sort(key=lambda name: -found[name])
    start, failed, total, skipped, timings = time.monotonic(), [], 0, 0, []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for future in as_completed([pool.submit(run, name) for name in names]):
            name, code, text, seconds, ran, skip = future.result()
            total, skipped = total + ran, skipped + skip
            timings.append((seconds, name))
            if code:
                failed.append(name)
                print(f'FAIL {name} ({seconds:.1f}s)\n{text.rstrip()}\n', flush=True)
    for seconds, name in sorted(timings, reverse=True)[:args.slowest]:
        print(f'{seconds:6.1f}s  {name}')
    print(f"{total} tests in {len(names)} classes, {skipped} skipped, {len(failed)} failed classes, wall {time.monotonic() - start:.0f}s")
    for name in failed:
        print(f'  rerun: python3 -m unittest {name}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
