#!/usr/bin/env python3
"""Run the unittest suite in parallel: one process per test, standard library only.

    python3 -B scripts/run_tests.py            # everything, one worker per CPU
    python3 -B scripts/run_tests.py -k update  # tests whose id contains "update"
    python3 -B scripts/run_tests.py -j 1       # serial

Each test runs as its own ``python -B -m unittest ID`` process, so a test that patches the process environment,
rebinds a module function or crashes on purpose stays isolated exactly as under ``python -m unittest MODULE``,
and one class with many slow tests no longer runs them one after another while other workers sit idle.
Output is shown only for a test that fails.
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


def tests(suite, found):
    """Test ids grouped by class, in discovery order."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            tests(item, found)
        else:
            found.setdefault(f'{type(item).__module__}.{type(item).__qualname__}', []).append(item.id())
    return found


def run(name):
    start = time.monotonic()
    done = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', name], cwd=ROOT, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    ran = re.search(r'^Ran (\d+) test', done.stdout, re.MULTILINE)
    skipped = re.search(r'skipped=(\d+)', done.stdout)
    return name, done.returncode, done.stdout, time.monotonic() - start, int(ran.group(1)) if ran else 0, int(skipped.group(1)) if skipped else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('-j', '--jobs', type=int, default=os.cpu_count() or 4, help='parallel processes (default: CPU count)')
    parser.add_argument('-k', dest='pattern', action='append', default=[], help='only tests whose dotted id contains this text; repeatable')
    parser.add_argument('--slowest', type=int, default=0, metavar='N', help='also list the N slowest tests')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    found = tests(unittest.TestLoader().discover(str(ROOT / 'tests'), top_level_dir=str(ROOT)), {})
    broken = [name for name in found if name.startswith('unittest.loader.')]
    if broken:
        print('A test module failed to import; run python3 -m unittest discover -s tests -t . to see it.')
        return 1
    # Tests of the largest classes first: those are the slow integration tests, so they do not start last and set the wall time.
    names = [name for owner in sorted(found, key=lambda owner: -len(found[owner])) for name in found[owner]
             if not args.pattern or any(text in name for text in args.pattern)]
    if not names:
        print('No tests match.')
        return 1
    start, failed, total, skipped, timings = time.monotonic(), [], 0, 0, []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for future in as_completed([pool.submit(run, name) for name in names]):
            name, code, text, seconds, ran, skip = future.result()
            total, skipped = total + ran, skipped + skip
            timings.append((seconds, name))
            if skip:
                reason = re.search(r"\.\.\. skipped (.+)", text)
                print(f"SKIP {name}: {reason.group(1) if reason else 'reason unavailable'}", flush=True)
            if code:
                failed.append(name)
                print(f'FAIL {name} ({seconds:.1f}s)\n{text.rstrip()}\n', flush=True)
    for seconds, name in sorted(timings, reverse=True)[:args.slowest]:
        print(f'{seconds:6.1f}s  {name}')
    classes = len({name.rsplit('.', 1)[0] for name in names})
    print(f"{total} tests in {classes} classes, {skipped} skipped, {len(failed)} failed, wall {time.monotonic() - start:.0f}s")
    for name in sorted(failed):
        print(f'  rerun: python3 -m unittest {name}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
