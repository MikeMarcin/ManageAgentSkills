# Contributing to ManageAgentSkills

Use the live RFC and local issue-board contracts. The implement-rfc skill automates this process, but human contributors can satisfy the same requirements without a particular agent. Read root/nested instructions, claim a bounded card, implement only owned paths, run focused acceptance checks, keep docs truthful, and commit explicit paths.

Do not treat a detailed RFC packet as completed work. Record actual baseline/integration commits and leave unavailable native-platform cards open. No mandatory broad test matrix or model/runtime subscription is implied. Tests use disposable local fixtures; live private source/auth changes require explicit scope.

Use existing Git authentication and avoid adding credentials to skills, config, output or logs. Public projects must keep their contributor contract readable without access to private skill content.

Original code and documentation contributions use the repository's
[MIT License](LICENSE). Preserve third-party copyright, license notices and
provenance when adapting material. Tap packages and dependencies keep their own
terms, as described in the [license scope](README.md#license).

For opt-in local secret checks, run `python3 -B scripts/betterleaks.py setup`,
then `python3 -B scripts/betterleaks.py staged`. The
[local scanning guide](docs/development/local-secret-scanning.md) covers tracked
source/history scans and safe pre-commit hook installation. BetterLeaks runs
locally only; it is separate from the standard test suite and GitHub workflows.

When changing shared skill content, edit the canonical AgentSkills source through ordinary Git, not a per-project copy. MASK links consumers to locked store copies of a tap, so an edit reaches them only after it is pushed and `mask upgrade` runs (or through an explicit `skill dev-link`). MASK can explicitly commit changed project selections and locks with `upgrade --commit`, including their existing uncommitted changes. It preserves unrelated staging and runs normal Git hooks and signing after readiness succeeds. MASK never pushes or synchronizes edits back to skill sources. During the one-time bootstrap phase, follow the recorded temporary-copy instructions and retire those copies at cutover.

## Fresh source checkout

Use Python 3.11+ and Git. Runtime MASK uses the standard library. Its own test
suite has no third-party Python dependency. The documentation gate uses the
canonical AgentSkills board helpers; clone that companion explicitly (or pass an
existing reviewed source checkout), without installing skills into your profile:

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
git clone https://github.com/MikeMarcin/AgentSkills.git
cd ManageAgentSkills
python3 -B scripts/verify_documentation.py --root . --agent-skills ../AgentSkills
python3 -B -m unittest tests.test_end_to_end.EndToEndTests.test_public_management_sequence
python3 -B scripts/run_tests.py -j 6 --slowest 5
```

Before the public switch, the companion requires your existing authorized Git
access. Missing or invalid companion source fails the documentation check with
an actionable error. `scripts/allocate_issue_id.py --agent-skills ../AgentSkills`
also supports contributors without an installed workflow. AgentSkills owns the
helpers; do not vendor private installed copies into MASK.

For cross-repository checks, create a Python virtual environment, install the
companion's `requirements-dev.txt`, and run its `verify_mask_examples.py`,
`verify_rfc_bundle.py`, and `verify_selected_skill_imports.py` with
`--mask-program /absolute/path/to/ManageAgentSkills`. These exercise disposable
consumers through the real MASK CLI. Public CI requires the explicit companion
checkout and documentation/integration checks. Private preparation CI runs the
MASK suite and declares companion checks as local-only; it uses no extra token.

Native Windows/macOS qualification and attended consumer migrations remain on
their live cards. Linux CI fixtures establish only the tested Linux behavior.
The owner adopted MIT for original contributions on 2026-10-14. Repository
visibility remains a separate owner action; the staged trust roadmap is not a
completed signed release channel. After both repositories become public,
manually dispatch each Source checks workflow to verify its companion checks.
