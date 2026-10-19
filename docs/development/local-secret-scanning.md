# Local secret scanning

This repository offers an opt-in local BetterLeaks check. Set it up explicitly
from the checkout root with Python 3.11+ and Git:

```sh
python3 -B scripts/betterleaks.py setup
python3 -B scripts/betterleaks.py staged
python3 -B scripts/betterleaks.py install-hook
```

Setup downloads the official **1.9.0** release into the ignored `.tools/` cache,
checks its pinned archive SHA-256, and checks the executable's exact version.
Re-running setup reuses that version. Scans and commits never install or download
anything. Missing or mismatched binaries fail with instructions to run setup;
move an unexpected cached binary aside before retrying setup. This does not use
Homebrew, global Git configuration, MASK state or another consumer's tools.

The release source and checksums are pinned in
[`scripts/betterleaks.py`](../../scripts/betterleaks.py), using the
[official v1.9.0 release](https://github.com/betterleaks/betterleaks/releases/tag/v1.9.0).
Version upgrades require reviewing that source, flags, checksums and rules again.

Run these checks when needed:

```sh
# Added lines in the Git index, including partially staged files:
python3 -B scripts/betterleaks.py staged
# Full current contents of tracked working files, including unstaged edits:
python3 -B scripts/betterleaks.py tracked
# Added lines in complete locally available history across all refs:
python3 -B scripts/betterleaks.py history
```

The staged command checks the index Git is about to commit, including Git's
temporary index for `git commit -a`. It does not check unstaged or untracked
files. The tracked command exports tracked working files into a temporary
directory; deleted files have no current content. It scans symlink target text
without following symlinks and refuses linked parent directories or submodules.
The history command includes local branches and locally stored remote refs,
requires a complete clone, and never fetches. Unreferenced objects, reflogs,
commit messages, untracked files and other repositories are outside this check.

Every scan uses the pinned binary's embedded rules through an explicit temporary
configuration. Ambient BetterLeaks/Gitleaks config, local config discovery,
ignore files and allow comments cannot suppress checks. Live credential
validation is disabled; only local Git/directory sources are invoked. Recursive
decoding and archive scanning use explicit depths of 5 and 8. The embedded rules'
own filters still apply; scanner success is not proof that every possible secret
format is absent.

BetterLeaks 1.9.0 reads source-directory ignore files even when an explicit empty
ignore file is selected. The wrapper therefore refuses a checkout containing
`.betterleaksignore` or `.gitleaksignore`, including untracked ones, and preserves
their contents. Review and move those files aside explicitly before scanning;
this error cannot be mistaken for a clean result.

The only repository exception applies to `generic-credential-uri`, the exact
files `tests/test_tap_identity.py`, `tests/test_sources.py`, `tests/test_ensure.py`,
and the literal synthetic password values `secret`, `token` or `TOPSECRET` at
their intersection. Those existing tests reject credential-bearing URLs. Other
passwords, rules, test files and documentation retain detection.

Output contains finding locations and rule names. Secret text, matches,
surrounding lines and scanner diagnostics are withheld; temporary reports are
fully redacted and removed. Exit status is **0** for a clean scan, **1** for
findings and **2** for setup or scan errors. Resolve findings before committing;
an error is not a clean scan.

`install-hook` creates an executable repository `pre-commit` hook and is
idempotent. It refuses any existing different hook, any configured
`core.hooksPath`, linked hooks directories and linked worktrees whose hooks
would affect the primary checkout. Existing hook users can explicitly add
`python3 -B scripts/betterleaks.py staged` to their own hook while preserving its
other checks. Installing in a primary checkout also covers its linked worktrees;
each such checkout needs the script and its own setup cache. To remove only this
integration's unchanged hook:

```sh
python3 -B scripts/betterleaks.py uninstall-hook
```

Focused disposable-fixture checks require explicit setup first:

```sh
python3 -B scripts/check_betterleaks.py
```

These checks live outside standard test discovery. No GitHub workflow, standard
test entrypoint or MASK command installs or invokes BetterLeaks. Neither scanner
execution nor scanner setup adds GitHub Actions work. Local commits run the
opt-in hook only where a contributor installs it.

The integration and real release have been exercised on macOS ARM64. Setup has
pinned macOS/Linux x64 and ARM64 and Windows x64/ARM64 archives; those other native
platforms have not been verified by this milestone. Windows hooks require Git's
shell and an available `python3`, matching the commands above.
