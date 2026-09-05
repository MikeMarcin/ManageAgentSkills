"""Exercise the source dump's public CLI using disposable project roots."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/make_project_source_dumps.py"
DEFAULT_OUTPUT = "artifacts/manage_agent_skills_project_source.md"


class ProjectSourceDumpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "fixture with spaces"
        self.write("README.md", "# Fixture\n")
        self.write("mask.py", "print('working tree')\n")
        self.write("schemas/project.schema.json", "{}\n")

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_dump(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--root", str(self.root), *args],
            cwd=self.root.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_manifest_contains_working_tree_and_portable_context(self):
        self.write("tests/test_example.py", "# newly created source\n")
        self.write("docs/guide.md", "# Guide\n`````python\nx = 1\n`````\n")
        self.write(".mask.json", "{}\n")
        self.write(".mask/skill-config/implement-rfc/project.md", "# Context\n")
        self.write("docs/issues/NEXT_ID", "MASK-0001\n")
        self.write("docs/assets/header.svg", "<svg/>\n")
        result = self.run_dump("--stdout")
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = result.stdout.split("```text\n", 1)[1].split("\n```", 1)[0]
        self.assertTrue(manifest.startswith("README.md [repository-context]\n"))
        for entry in (
            "mask.py [source]",
            "tests/test_example.py [test]",
            "schemas/project.schema.json [schema]",
            ".mask.json [project-config]",
            ".mask/skill-config/implement-rfc/project.md [workflow-context]",
            "docs/issues/NEXT_ID [docs]",
            "docs/assets/header.svg [docs]",
        ):
            self.assertIn(entry, manifest)
        self.assertIn("print('working tree')", result.stdout)
        self.assertIn("``````markdown\n# Guide\n`````python\nx = 1\n`````\n``````", result.stdout)
        self.assertFalse((self.root / DEFAULT_OUTPUT).exists())

    def test_exclusions_remain_in_effect_with_generated_opt_in(self):
        excluded = (
            ".git/private.md", ".venv/lib/package.py", "venv/lib/package.py",
            "__pycache__/cache.py", ".pytest_cache/cache.md", ".cache/cache.json",
            "package.egg-info/metadata.txt", "node_modules/package/index.json",
            ".mask/generated/agents.md", ".mask/bootstrap-retired/old/SKILL.md",
            ".mask/sessions/private.json", ".mask/state.json",
            ".agents/skills/local/SKILL.md", ".claude/settings.json",
            ".codex/agents/worker.toml", "docs/archive.zip", ".DS_Store",
        )
        for relative in excluded:
            self.write(relative, "EXCLUDED CONTENT\n")
        self.write("build/generated.py", "BUILD CONTENT\n")
        self.write("artifacts/previous.md", "PREVIOUS OUTPUT\n")
        for args in ((), ("--include-generated",)):
            with self.subTest(args=args):
                result = self.run_dump("--stdout", *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("EXCLUDED CONTENT", result.stdout)
                self.assertEqual("BUILD CONTENT" in result.stdout, bool(args))
                self.assertEqual("PREVIOUS OUTPUT" in result.stdout, bool(args))

    def test_does_not_follow_file_or_directory_links(self):
        external = self.root.parent / "external"
        external.mkdir()
        (external / "outside.md").write_text("LINKED CONTENT", encoding="utf-8")
        try:
            (self.root / "linked").symlink_to(external, target_is_directory=True)
            (self.root / "linked.md").symlink_to(external / "outside.md")
            (self.root / "broken.py").symlink_to(external / "missing.py")
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        result = self.run_dump("--stdout", "--include-generated")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("LINKED CONTENT", result.stdout)
        self.assertNotIn("broken.py", result.stdout)

    def test_output_destinations_are_rerunnable_and_exclude_themselves(self):
        for destination in (DEFAULT_OUTPUT, "custom.md", str(self.root.parent / "absolute.md")):
            with self.subTest(destination=destination):
                output = self.root / destination
                for _ in range(2):
                    result = self.run_dump("--output", destination, "--include-generated")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    text = output.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith("# ManageAgentSkills Project Source\n"))
                    self.assertNotIn(f"### {destination}\n", text)
                output.unlink()

    def test_default_output(self):
        result = self.run_dump()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / DEFAULT_OUTPUT).is_file())

    def test_invalid_roots_and_invalid_text_report_errors(self):
        result = self.run_dump("--root", str(self.root / "missing"))
        self.assertEqual(result.returncode, 2)
        result = self.run_dump("--root", str(self.root.parent))
        self.assertEqual(result.returncode, 2)
        for content in (b"\xff", b"binary\0content"):
            with self.subTest(content=content):
                (self.root / "invalid.py").write_bytes(content)
                result = self.run_dump()
                self.assertEqual(result.returncode, 1)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((self.root / DEFAULT_OUTPUT).exists())


if __name__ == "__main__":
    unittest.main()
