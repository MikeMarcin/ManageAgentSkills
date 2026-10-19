#!/usr/bin/env python3
"""Explicit local BetterLeaks checks; deliberately outside standard test discovery."""
from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import random
import shutil
import string
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import betterleaks as local

SCRIPT = Path(local.__file__).resolve()


class LocalChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mask-local-scanner-check-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.env = local.local_environment()
        self.env.pop("GIT_INDEX_FILE", None)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "data.txt").write_text("ordinary public source\n")
        self.git("add", "data.txt")
        self.git("commit", "-m", "clean fixture")
        alphabet = list(string.ascii_letters + string.digits)
        random.Random(145).shuffle(alphabet)
        # Construct a synthetic detector sample only in disposable fixtures.
        self.sample = "ghp_" + "".join(alphabet[:36])

    def git(self, *args, expected=0):
        result = subprocess.run(["git", "-C", str(self.repo), *args], env=self.env, capture_output=True)
        self.assertEqual(result.returncode, expected, "fixture Git operation failed")
        return result

    def command(self, mode, expected=0, script=SCRIPT, env=None):
        result = subprocess.run([sys.executable, "-B", str(script), mode, "--repo", str(self.repo)],
                                cwd=self.root, env=env or self.env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        self.assertTrue(self.sample not in output, "secret sample escaped redaction")
        self.assertEqual(result.returncode, expected, output)
        return output

    def sample_file(self, path="data.txt"):
        (self.repo / path).write_text("github_token = " + self.sample + "\n")

    def checkout_script(self, tool=True):
        destination = self.repo / "scripts" / SCRIPT.name
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(SCRIPT, destination)
        binary = self.repo / local.tool_location()[1].relative_to(local.SOURCE_ROOT)
        if tool:
            binary.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local.tool_location()[1], binary)
        return destination, binary

    def test_partial_index_and_tracked_source(self):
        self.command("staged")
        self.sample_file("untracked.txt")
        self.command("tracked")
        self.sample_file()
        self.git("add", "data.txt")
        (self.repo / "data.txt").write_text("clean unstaged version\n")
        output = self.command("staged", 1)
        self.assertIn("github-pat", output)
        self.command("tracked")
        self.git("add", "data.txt")
        self.sample_file()
        self.command("staged")
        self.command("tracked", 1)

    def test_history_reads_other_local_refs(self):
        self.git("checkout", "-b", "fixture-history")
        self.sample_file()
        self.git("add", "data.txt")
        self.git("commit", "-m", "synthetic fixture only")
        self.git("checkout", "main")
        self.command("tracked")
        self.command("history", 1)
        (self.repo / ".git" / "shallow").write_bytes(self.git("rev-parse", "HEAD").stdout)
        self.assertIn("complete local clone", self.command("history", 2))

    def test_ambient_config_ignores_and_allow_comments_cannot_suppress(self):
        (self.repo / ".betterleaks.toml").write_text("prefilter = 'true'\n")
        (self.repo / ".gitleaks.toml").write_text("prefilter = 'true'\n")
        (self.repo / "data.txt").write_text("github_token = " + self.sample +
                                            " # betterleaks:allow gitleaks:allow\n")
        self.git("add", "data.txt")
        env = dict(self.env, BETTERLEAKS_CONFIG_TOML="prefilter = 'true'",
                   GITLEAKS_CONFIG=str(self.repo / ".gitleaks.toml"), BETTERLEAKS_VALIDATION="true")
        self.command("staged", 1, env=env)
        self.command("tracked", 1, env=env)
        for name in (".betterleaksignore", ".gitleaksignore"):
            # Caller cwd is outside --repo; its ignore must not affect the target.
            caller_ignore = self.root / name
            caller_ignore.write_text("data.txt:github-pat:1\n")
            self.command("staged", 1, env=env)
            ignore = self.repo / name
            ignore.write_text("data.txt:github-pat:1\n")
            for mode in ("staged", "tracked", "history"):
                self.assertIn("Source ignore files", self.command(mode, 2, env=env))
            self.assertEqual(ignore.read_text(), "data.txt:github-pat:1\n")
            ignore.unlink()
            caller_ignore.unlink()

    def test_fixture_allowlist_is_intersection(self):
        folder = self.repo / "tests"
        folder.mkdir()
        # Only a known fake password, in the named rule and file, is exempted.
        fake_uri = "https://user:" + "secret@example.invalid/org/repo"
        (folder / "test_sources.py").write_text(fake_uri + "\n")
        self.git("add", "tests/test_sources.py")
        self.command("staged")
        self.command("tracked")
        (self.repo / "data.txt").write_text(fake_uri + "\n")
        self.git("add", "data.txt")
        self.command("staged", 1)
        self.command("tracked", 1)
        (self.repo / "data.txt").write_text("clean\n")
        self.git("add", "data.txt")
        self.sample_file("tests/test_sources.py")
        self.git("add", "tests/test_sources.py")
        self.command("staged", 1)

    def test_real_hook_and_alternate_commit_index(self):
        script, _ = self.checkout_script()
        self.command("install-hook", script=script)
        owned = self.repo / ".git" / "hooks" / "pre-commit"
        self.assertEqual(owned.read_bytes(), local.HOOK)
        self.command("install-hook", script=script)
        self.sample_file()
        self.git("add", "data.txt")
        failed = self.git("commit", "-m", "must refuse", expected=1)
        self.assertTrue(self.sample.encode() not in failed.stdout + failed.stderr, "hook leaked sample")
        (self.repo / "data.txt").write_text("clean new content\n")
        self.git("add", "data.txt")
        self.git("commit", "-m", "clean hook succeeds")
        self.sample_file()
        failed = self.git("commit", "-a", "-m", "alternate index must refuse", expected=1)
        self.assertTrue(self.sample.encode() not in failed.stdout + failed.stderr, "alternate index leaked sample")
        self.command("uninstall-hook", script=script)
        self.assertFalse(owned.exists())

    def test_hook_collisions_and_custom_path_are_preserved(self):
        script, _ = self.checkout_script()
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 0\n")
        original = hook.read_bytes()
        self.command("install-hook", 2, script=script)
        self.command("uninstall-hook", 2, script=script)
        self.assertEqual(hook.read_bytes(), original)
        hook.unlink()
        self.git("config", "core.hooksPath", "custom-hooks")
        self.command("install-hook", 2, script=script)
        self.assertFalse(hook.exists())
        self.assertEqual(self.git("config", "--get", "core.hooksPath").stdout.strip(), b"custom-hooks")

    def test_missing_wrong_and_failing_binary_never_expose_output(self):
        script, binary = self.checkout_script(tool=False)
        self.assertIn("setup", self.command("staged", 2, script=script))
        if os.name == "nt":
            self.skipTest("POSIX fake executable negative controls")
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text("#!/bin/sh\nprintf '2.0.0\\n'\n")
        binary.chmod(0o755)
        self.assertIn("exactly 1.9.0", self.command("staged", 2, script=script))
        binary.write_text("#!/bin/sh\nif [ \"$1\" = version ]; then printf '1.9.0\\n'; exit 0; fi\n"
                          "printf '%s' '" + self.sample + "' >&2\nexit 2\n")
        self.command("staged", 2, script=script)

    def test_setup_checksum_and_scan_has_no_download_path(self):
        # Wrong archive bytes fail before extraction/publication.
        with mock.patch.object(local, "SOURCE_ROOT", self.repo), \
             mock.patch.object(local.urllib.request, "urlopen", return_value=io.BytesIO(b"not a release")), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(local.CheckError, "SHA-256 mismatch"):
                local.setup()
            self.assertFalse(local.tool_location()[1].exists())
        real_run = subprocess.run
        calls = []

        def recorded(*args, **kwargs):
            calls.append((args[0], kwargs.get("env", {})))
            return real_run(*args, **kwargs)

        with mock.patch.object(local.urllib.request, "urlopen", side_effect=AssertionError("scan downloaded")), \
             mock.patch.object(local.subprocess, "run", side_effect=recorded), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(local.scan(self.repo, "staged"), 0)
        invocation, environment = calls[-1]
        self.assertIn("--validation=false", invocation)
        self.assertIn("--redact=100", invocation)
        self.assertIn("--staged", invocation)
        self.assertFalse(any(key.startswith(("BETTERLEAKS_", "GITLEAKS_")) for key in environment))


if __name__ == "__main__":
    # Missing setup is an error, never a passing skip in a CI environment.
    local.check_version(local.tool_location()[1])
    unittest.main(verbosity=2)
