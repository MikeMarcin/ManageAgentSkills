"""Retired live-checkout commands in help, capabilities and current documentation (RFC-MASK-0021 AC05/AC06; cases D01, D03; MASK-0105).

The retired spellings are the four the retained contract names (``contracts/CLI.md``, "Help and documentation"),
the other removed ``init`` options and the removed top-level ``migrate`` command. Current documentation is every
Markdown file of this repository except historical records: the RFC tree (retained packets under ``docs/rfcs/assets``,
RFC text and plans), the issue board's card records of that RFC work, release reports, and the dated evidence
reports named in ``HISTORICAL``. The RFC keeps historical RFCs and evidence unchanged. Inside the migration guide only
its old-command table may name a retired spelling.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import mask
import mask_present as present

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'mask.py'
RETIRED = re.compile(r'(?<![\w-])init\s+--(?:source|remote|branch)\b'
                     r'|(?<![\w-])source\s+(?:status|migrate)\b'
                     r'|(?<![\w-])migrate\s+--to-pinned\b'
                     r'''|\bmask(?:\.py|\.cmd)?["']?\s+migrate\b''')
CONTRACT_SPELLINGS = ('init --source', 'source status', 'source migrate', 'migrate --to-pinned')
HISTORICAL_ROOTS = ('docs/rfcs/', 'docs/issues/', 'docs/releases/')
HISTORICAL = {
    'docs/development/corrective-baseline.md': 'RFC-MASK-0018 public baseline evidence, recorded on the live-checkout program',
    'docs/development/tap-cutover-baseline.md': 'RFC-MASK-0021 pre-implementation baseline evidence (MASK-0100)',
}
MIGRATION_GUIDE = 'docs/guides/migration-and-pins.md'
OLD_COMMANDS = re.compile(r'^#{2,4} Old commands\b.*$', re.M)


def documents():
    """Every Markdown file outside hidden directories, plus the consumer workflow context under ``.mask/skill-config``."""
    found = []
    for directory, subdirectories, files in os.walk(ROOT):
        relative = Path(directory).relative_to(ROOT)
        keep = [name for name in subdirectories if name != '__pycache__' and not name.startswith('.')]
        if relative == Path('.'):
            keep += [name for name in subdirectories if name == '.mask']
        elif relative == Path('.mask'):
            keep = [name for name in subdirectories if name == 'skill-config']
        subdirectories[:] = keep
        found.extend((relative / name).as_posix() for name in files if name.endswith('.md'))
    return sorted(found)


def historical(relative):
    return relative.startswith(HISTORICAL_ROOTS) or relative in HISTORICAL


def table_lines(text):
    """1-based line numbers of the first Markdown table under the migration guide's "Old commands" heading."""
    heading = OLD_COMMANDS.search(text)
    if heading is None:
        return set()
    lines = text.splitlines()
    index = text.count('\n', 0, heading.start()) + 1
    while index < len(lines) and not lines[index].lstrip().startswith('|'):
        if lines[index].startswith('#'):
            return set()
        index += 1
    rows = set()
    while index < len(lines) and lines[index].lstrip().startswith('|'):
        rows.add(index + 1)
        index += 1
    return rows


def violations(text, exempt_lines=()):
    return [f"line {text.count(chr(10), 0, match.start()) + 1}: {' '.join(match.group(0).split())}"
            for match in RETIRED.finditer(text) if text.count('\n', 0, match.start()) + 1 not in exempt_lines]


class RetiredSpellingPattern(unittest.TestCase):
    def test_pattern_matches_retired_spellings_and_spares_current_ones(self):
        for text in (*CONTRACT_SPELLINGS, 'init --remote origin', 'mask init\n--branch main', 'mask migrate', 'mask.py" migrate --all',
                     'python3 mask.py source\nmigrate --json'):
            with self.subTest(text=text):
                self.assertTrue(RETIRED.search(text))
        for text in ('mask doctor --migrate --dry-run', 'doctor --migrate --project P --alias NAME', 'source dev-link ID --to-pinned',
                     'mask init --target codex', 'whole-source status', 'source fetch', '--expect-source PATH', 'migration.required'):
            with self.subTest(text=text):
                self.assertIsNone(RETIRED.search(text))


class HelpAndCapabilities(unittest.TestCase):
    """D01: every help page renders and names no retired command; capabilities is exactly the registered command table."""

    def test_every_help_page_renders_without_a_retired_spelling(self):
        parser, leaves = mask.make_parser()
        groups = sorted({name.split('.')[0] for name in mask.COMMANDS if '.' in name})
        pages = {(): mask.help_text(parser, leaves, [])}
        pages.update({(group,): mask.help_text(parser, leaves, [group]) for group in groups})
        pages.update({tuple(command.split('.')): mask.help_text(parser, leaves, command.split('.')) for command in mask.COMMANDS})
        self.assertEqual(len(pages), 1 + len(groups) + len(mask.COMMANDS))
        for words, text in pages.items():
            with self.subTest(help=' '.join(('mask', *words, '--help'))):
                self.assertTrue(text.strip())
                self.assertEqual(violations(text), [])

    def test_presentation_tables_name_only_registered_commands(self):
        self.assertEqual(sorted(set(present.COMMAND_HELP) - set(mask.COMMANDS)), [])
        self.assertEqual(sorted(set(present.RENDERERS) - set(mask.COMMANDS) - {'help', 'version'}), [])

    def test_public_help_and_capabilities(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, MASK_HOME=home, NO_COLOR='1')
            run = lambda *args: subprocess.run([sys.executable, '-B', str(ENTRY), *args], capture_output=True, encoding='utf-8',
                                               env=env, stdin=subprocess.DEVNULL, timeout=60)
            for args in (('--help',), ('upgrade', '--help'), ('doctor', '--help')):
                with self.subTest(args=args):
                    shown = run(*args)
                    self.assertEqual((shown.returncode, shown.stderr), (0, ''))
                    self.assertTrue(shown.stdout.strip())
                    self.assertEqual(violations(shown.stdout), [])
            described = run('capabilities', '--json')
            self.assertEqual(described.returncode, 0, described.stderr)
            data = json.loads(described.stdout)['data']
            self.assertEqual([item['name'] for item in data['commands']], list(mask.COMMANDS))
            self.assertEqual((data['deployment_model'], data['migration'], data['schemas']['machine']), ('taps', 'doctor', 3))
            self.assertEqual(violations(' '.join(item['name'].replace('.', ' ') for item in data['commands'])), [])


class CurrentDocumentation(unittest.TestCase):
    """D03: retired spellings appear only in historical records and in the migration guide's old-command table."""

    def test_current_documentation_names_no_retired_command(self):
        current = [relative for relative in documents() if not historical(relative)]
        self.assertIn('README.md', current)
        self.assertIn('docs/architecture/cli-contract.md', current)
        self.assertIn('.mask/skill-config/implement-rfc/project.md', current)
        for relative in current:
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding='utf-8')
                exempt = table_lines(text) if relative == MIGRATION_GUIDE else ()
                self.assertEqual(violations(text, exempt), [])

    def test_migration_guide_maps_every_retired_spelling_in_its_old_command_table(self):
        text = (ROOT / MIGRATION_GUIDE).read_text(encoding='utf-8')
        rows = table_lines(text)
        self.assertTrue(rows, 'the migration guide needs a table under an "Old commands" heading')
        table = '\n'.join(text.splitlines()[number - 1] for number in sorted(rows))
        for spelling in CONTRACT_SPELLINGS:
            with self.subTest(spelling=spelling):
                self.assertIn(spelling, table)

    def test_historical_exemptions_exist(self):
        for relative in HISTORICAL:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())


if __name__ == '__main__':
    unittest.main()
