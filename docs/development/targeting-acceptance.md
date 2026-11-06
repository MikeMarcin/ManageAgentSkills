# Native pinning and agent targeting

Stage B qualifies exact artifact deployment and independent Claude/Codex
selection for projects and the personal scope. Test packages, Git remotes,
consumer roots and MASK homes were disposable.

| Lane | Tested source | Environment | Evidence |
|---|---|---|---|
| macOS | `74f341a36791887f747373a0db37addd03b9c47e` | macOS 26.6.2 arm64, Python 3.15.0, Apple Git 2.50.1 | Public CLI composition and focused suite below |
| Windows | `7b6c6dbfa164fe6e01f5ca0f7b350b710b92cf30` | Windows 11, Python 3.14, Git 2.55, `core.autocrlf=true` | Clean-worktree `python -B scripts/run_tests.py` reported 581 tests, 40 skipped and zero failures in 830 s. [MASK-0136](../issues/60-done/MASK-0136-windows-test-failures.md) |

## Public macOS composition

The subprocess entry point was `python3 -B mask.py … --json`, with a local
bare tap, fixture `MASK_HOME`, and both home variables redirected. The fixture
installed the same skill into the project and personal scope. Default project
installation produced both `.claude/skills/alpha` and `.agents/skills/alpha`.
Personal installation selected Claude only. The project then selected Codex
only via `project set-agents`, retaining the exact package resolution. The
first probe used the older engine-only `--apply` flag and exited 2. The
current public setter applies by default, and the corrected probe passed.

The initial links resolved to the same store artifact. Authoring and moving
the upstream ref left both locks and deployed bytes unchanged. A scoped
`upgrade TAP/alpha --project PATH --no-update` fetched and activated the new
exact bytes for the project, leaving the personal lock, link and bytes intact.
Repeating the unchanged agent choice was a no-op. The fixture directory was
removed after both probes.

```sh
python3 -B scripts/run_tests.py -j 6 \
  -k test_targeting -k test_user_scope -k test_pinned_recovery \
  -k test_compatibility -k test_adapters -k test_selection_conflicts \
  -k test_pinned_update -k test_artifacts -k test_locks -k test_link_producers \
  -k test_stable_locks -k test_recovery_entrypoint -k test_upgrade_groups \
  -k test_u05_moved_tag_refuses -k test_install_dry_run_refusal_and_native_forwarding \
  --slowest 7
```

The focused suite passed all 121 tests in 27 classes in 410 seconds, with
zero skips. A separate public recovery probe crashed at link activation.
Recovery completed after a forward commit that changed only an unrelated
file. Committing an `AGENTS.md` change instead caused `recovery.conflict`
and preserved the journal and fixture.

## Windows coverage carried forward

At the Windows-tested revision, the discovery runner selected the scope,
targeting, compatibility, collision and adapter cases in
`test_targeting`, `test_user_scope`, `test_compatibility`, `test_adapters`
and `test_selection_conflicts`. The following were regular runnable cases
without Windows skip conditions:

- `test_independent_agents_inheritance_noop_and_declaration_only` exercised
  the same skill in independent personal and project scopes with real
  Claude/Codex directory links, a preserved package lock and a repeat no-op.
- `test_membership_agents_and_home_are_independent` and
  `test_linked_parent_and_cross_scope_overlap_refuse` exercised the physical
  personal home boundary, including a Unicode path, store targets and link
  ownership. `test_collision_preflights_both_scopes_and_declaration_edit`
  required an occupied leaf to survive a refused apply.
- `test_false_when_skips_cold_package_and_preserves_lock` and
  `test_cold_specific_implicit_exclusion_explicit_block_and_requirements`
  distinguished conditional omission from incompatible explicit selection.
  The other compatibility tests covered assertion levels and scoped overrides.
- `test_public_disjoint_agents_and_collision_preserve_controls_and_content`
  and the scope-shadowing cases exercised overlapping and disjoint agent
  names. Adapter tests checked path, capability, schema and package boundaries.

The five test modules, their runner fixture and the selection, adapter,
filesystem planner, lock resolver and store modules match `74f341a`. The
Windows full suite also included pinning, artifact restore, publication and
typed recovery. The macOS run exercised grouped upgrades, and the separate
probe exercised forward-commit recovery. Directory rebinding has its own
acceptance record. [MASK-0115](../issues/60-done/MASK-0115-stable-directory-identity-across-reboot.md)

The September Windows attempt in
MASK-0040 remains historical, including its harness failure and UTF-8 fixture
correction. The accepted Windows result is the later full suite, whose
revision includes correction `69c740c`.

Native adapter acceptance here covers filesystem links, reporting and existing
launcher/prelaunch evidence. First-prompt host loading and native host gate
enforcement remain unverified. [Readiness acceptance](readiness-acceptance.md)

## Historical migration boundary

The original Stage B migration used `migrate --to-pinned`. MASK-0037
records passing personal and project migration, dirty and unborn source
refusals, pending recovery ordering, exact rollback and the prior-program
refusal with a direct Python fallback. MASK-0104 and MASK-0106 record the
successor doctor migration and native Windows rehearsal. [MASK-0037](../issues/60-done/MASK-0037-pin-migration.md) · [MASK-0104](../issues/60-done/MASK-0104-doctor-migration.md) · [Native rehearsal](readiness-acceptance.md#real-package-qualification-on-taps-rfc-mask-0021-mask-0106)

The owner later retired pre-tap configuration, deployment and recovery at
`7ccf671a726e073d6768551e460c6f1fbeca3c9b`, following the migration boundary
recorded in RFC-MASK-0021 mandate r4 Q5. This closeout uses the earlier results
for that historical capability. Current acceptance covers tap declarations,
pinned and explicit development links, and current recovery. First-prompt
loading and RFC-MASK-0021's real-machine dogfood remain in their existing
scope. [Owner decision](../rfcs/RFC-MASK-0021-tap-only-deployment.md)
