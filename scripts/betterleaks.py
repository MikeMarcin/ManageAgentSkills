#!/usr/bin/env python3
"""Opt-in local secret checks. Only `setup` accesses the network."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

VERSION = "1.9.0"
SOURCE_ROOT = Path(__file__).resolve().parents[1]
RELEASE = f"https://github.com/betterleaks/betterleaks/releases/download/v{VERSION}"
CHECKSUMS = {
    "darwin_arm64": "83dd7eaab13d44a1e8e347a17064cdef153a1478db473276d41b38d55613d3f2",
    "darwin_x64": "68dfd83458d9e7f90663daa7a81c7f944083b170dae82e4f5f8d0581ed519ef1",
    "linux_arm64": "1d39116e0a58dc94574715e2aa12a2dbd5062f193eee3fec011fef6ba06bd13b",
    "linux_x64": "f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7",
    "windows_arm64": "3e5b9b6cdbfe8d486ae2dd2fa137473dc9ab42bf50317f051b73561121861816",
    "windows_x64": "b765daec9fda475b031b5a5159798cbe4294a3f2a50683cbc0471226e376d3da",
}
HOOK = b"#!/bin/sh\n# MASK local BetterLeaks hook v1\nexec python3 -B scripts/betterleaks.py staged\n"
RECOVERY = "Run python3 -B scripts/betterleaks.py setup explicitly, then retry."
RULES = r"""[extend]
useDefault = true

# Existing rejection tests intentionally use these literal fake passwords.
# Keep the exception at the intersection of this rule, these files and values.
[[allowlists]]
description = "Synthetic URI passwords in source rejection fixtures"
targetRules = ["generic-credential-uri"]
condition = "AND"
paths = ['''^tests/test_(tap_identity|sources|ensure)\.py$''']
regexTarget = "secret"
regexes = ['''^(secret|token|TOPSECRET)$''']
"""


class CheckError(Exception):
    pass


def local_environment() -> dict[str, str]:
    # Preserve Git's temporary commit index (commit -a / pathspec commits).
    # No scanner config, credentials, Git command injection or global config.
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "TMPDIR", "TMP", "TEMP", "GIT_INDEX_FILE"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return env


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            env=local_environment())
    if result.returncode:
        raise CheckError("Git inspection failed; run from a local working checkout.")
    return result.stdout


def repository(path: Path) -> Path:
    return Path(os.fsdecode(git(path, "rev-parse", "--show-toplevel")).strip()).resolve()


def tool_location() -> tuple[str, Path]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {"aarch64": "arm64", "arm64": "arm64", "amd64": "x64", "x86_64": "x64"}.get(machine)
    target = f"{system}_{arch}"
    if target not in CHECKSUMS:
        raise CheckError("No pinned BetterLeaks release for this OS/architecture.")
    name = "betterleaks.exe" if system == "windows" else "betterleaks"
    return target, SOURCE_ROOT / ".tools" / "betterleaks" / VERSION / target / name


def check_version(binary: Path) -> None:
    if not binary.is_file() or binary.is_symlink():
        raise CheckError(f"Pinned BetterLeaks {VERSION} is missing. {RECOVERY}")
    try:
        result = subprocess.run([str(binary), "version"], capture_output=True,
                                env=local_environment(), timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CheckError(f"Pinned BetterLeaks cannot execute. {RECOVERY}") from exc
    if result.returncode or result.stdout.strip() != VERSION.encode():
        raise CheckError(f"BetterLeaks must be exactly {VERSION}. Move aside the cached binary. {RECOVERY}")


def setup() -> int:
    target, binary = tool_location()
    if binary.exists() or binary.is_symlink():
        check_version(binary)
        print(f"BetterLeaks {VERSION} already installed in the checkout cache.")
        return 0
    # Refuse linked cache parents; never install through a path to another checkout.
    for parent in binary.parents:
        if parent == SOURCE_ROOT:
            break
        if parent.is_symlink():
            raise CheckError("Tool cache contains a symlink; choose a regular checkout cache.")
    binary.parent.mkdir(parents=True, exist_ok=True)
    suffix = "zip" if target.startswith("windows_") else "tar.gz"
    asset = f"betterleaks_{VERSION}_{target}.{suffix}"
    print(f"Downloading official {asset} for explicit local setup.")
    with urllib.request.urlopen(f"{RELEASE}/{asset}", timeout=60) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != CHECKSUMS[target]:
        raise CheckError("Release SHA-256 mismatch; nothing installed.")
    # Read only the executable member, never extract archive-controlled paths.
    if suffix == "zip":
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            payload = package.read(binary.name)
    else:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
            member = package.getmember(binary.name)
            if not member.isfile():
                raise CheckError("Release executable is not a regular file.")
            with package.extractfile(member) as stream:
                payload = stream.read()
    with tempfile.TemporaryDirectory(prefix="setup-", dir=binary.parent) as work:
        candidate = Path(work) / binary.name
        candidate.write_bytes(payload)
        candidate.chmod(0o755)
        check_version(candidate)
        # Exclusive publication preserves any concurrent install/collision.
        with binary.open("xb") as destination:
            destination.write(payload)
        binary.chmod(0o755)
    print(f"Installed BetterLeaks {VERSION}; archive SHA-256 verified.")
    return 0


def tracked_snapshot(root: Path, destination: Path) -> None:
    for raw in git(root, "ls-files", "--cached", "-z").split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        if relative.is_absolute() or ".." in relative.parts:
            raise CheckError("Tracked path escapes the checkout.")
        source = root / relative
        # Do not follow a tracked symlink outside the checkout.
        if any((root / parent).is_symlink() for parent in relative.parents):
            raise CheckError("A tracked path has a linked parent; tracked scan refused.")
        output = destination / relative
        if source.is_symlink():
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(os.fsencode(os.readlink(source)))
        elif source.is_file():
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, output)
        elif source.exists():
            raise CheckError("Tracked directories/submodules require a separate explicit scan.")
        # Worktree deletions contain no current source to scan.


def scan(root: Path, mode: str) -> int:
    _, binary = tool_location()
    check_version(binary)  # Fail before doing any scan work; never auto-install.
    # v1.9.0 also reads source ignore files even with an explicit empty ignore.
    # Preserve them and fail closed instead of accepting suppressed findings.
    if any((root / name).exists() or (root / name).is_symlink()
           for name in (".betterleaksignore", ".gitleaksignore")):
        raise CheckError("Source ignore files are present; preserve/review them and move them aside before scanning.")
    if mode == "history" and git(root, "rev-parse", "--is-shallow-repository").strip() == b"true":
        raise CheckError("History scan requires a complete local clone; obtain its history explicitly before retrying.")
    with tempfile.TemporaryDirectory(prefix="mask-betterleaks-") as work:
        temporary = Path(work)
        config = temporary / "rules.toml"
        config.write_text(RULES, encoding="utf-8")
        ignore = temporary / "empty.ignore"
        ignore.touch()
        report = temporary / "report.json"
        options = ["--config", str(config), "--gitleaks-ignore-path", str(ignore),
                   "--ignore-gitleaks-allow", "--redact=100", "--validation=false",
                   "--no-banner", "--no-color", "--exit-code=10", "--report-format=json",
                   "--report-path", str(report), "--max-decode-depth=5", "--max-archive-depth=8"]
        if mode == "tracked":
            snapshot = temporary / "tracked"
            snapshot.mkdir()
            tracked_snapshot(root, snapshot)
            # Relative paths preserve the same rule/path exceptions as Git scans.
            args = ["dir", "."]
        else:
            args = ["git", str(root)]
            args += ["--staged", "--pre-commit"] if mode == "staged" else ["--log-opts=--all --full-history"]
        result = subprocess.run([str(binary), *args, *options], cwd=snapshot if mode == "tracked" else root,
                                env=local_environment(), capture_output=True)
        # Scanner diagnostics can include source text. Never forward them, even on error.
        if result.returncode not in (0, 10):
            raise CheckError(f"BetterLeaks {mode} scan failed (exit {result.returncode}); no scan accepted.")
        try:
            findings = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(findings, list) or any(not isinstance(f, dict) for f in findings):
                raise ValueError("invalid findings")
        except (OSError, ValueError) as exc:
            raise CheckError("BetterLeaks did not produce a valid report; no scan accepted.") from exc
        if bool(findings) != (result.returncode == 10):
            raise CheckError("BetterLeaks result/report disagree; no scan accepted.")
        for finding in findings:
            path = str(finding.get("File", ""))
            if mode == "tracked":
                path = path.removeprefix(str(snapshot) + os.sep)
            # JSON escapes control characters in paths; omit Match, Secret, message,
            # author and scanner diagnostics. No snippets or raw report are retained.
            location = {"file": path, "line": finding.get("StartLine"), "rule": finding.get("RuleID")}
            print(json.dumps(location, ensure_ascii=True))
        print(f"BetterLeaks {VERSION} {mode}: {len(findings)} finding(s); secret text withheld.")
        return 1 if findings else 0


def hook(root: Path, remove: bool = False) -> int:
    if root != SOURCE_ROOT:
        raise CheckError("Use the target checkout's own scripts/betterleaks.py to change its hook.")
    # Include global/system/environment config here so custom hooks are preserved.
    custom = subprocess.run(["git", "-C", str(root), "config", "--get-all", "core.hooksPath"],
                            capture_output=True)
    if custom.returncode != 1:
        raise CheckError("core.hooksPath is configured (or unreadable); preserve it and integrate the staged command manually.")
    common = Path(os.fsdecode(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")).strip())
    actual = Path(os.fsdecode(git(root, "rev-parse", "--absolute-git-dir")).strip())
    if common.resolve() != actual.resolve():
        raise CheckError("Linked worktrees share hooks; install from the primary checkout after reviewing that scope.")
    destination = common / "hooks" / "pre-commit"
    if destination.parent.is_symlink():
        raise CheckError("Hooks directory is a symlink; hook changes refused.")
    if destination.is_symlink() or (destination.exists() and
                                   (not destination.is_file() or destination.read_bytes() != HOOK)):
        raise CheckError("Existing pre-commit hook preserved; integrate the staged command manually.")
    if remove:
        if destination.exists():
            destination.unlink()
        print("Owned BetterLeaks hook removed (or already absent).")
    elif destination.exists():
        if not os.access(destination, os.X_OK):
            raise CheckError("Owned hook is not executable; review its permissions before reinstalling.")
        print("BetterLeaks pre-commit hook already installed.")
    else:
        check_version(tool_location()[1])
        if not (root / "scripts" / "betterleaks.py").is_file():
            raise CheckError("Checkout has no scripts/betterleaks.py; hook not installed.")
        destination.parent.mkdir(exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(HOOK)
        destination.chmod(0o755)
        print("Installed opt-in BetterLeaks pre-commit hook for this repository.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "staged", "tracked", "history", "install-hook", "uninstall-hook"])
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="local checkout to scan (default: current directory)")
    args = parser.parse_args()
    try:
        if args.command == "setup":
            return setup()
        root = repository(args.repo)
        if args.command in ("install-hook", "uninstall-hook"):
            return hook(root, remove=args.command == "uninstall-hook")
        return scan(root, args.command)
    except (CheckError, OSError, subprocess.SubprocessError, KeyError, tarfile.TarError, zipfile.BadZipFile) as exc:
        # Do not expose exception text from external libraries or untrusted sources.
        message = str(exc) if isinstance(exc, CheckError) else "Local BetterLeaks operation failed; no check accepted."
        print(message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
