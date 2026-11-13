# MASK-0153 engineering checkpoint

Assignment: `/root/implement_fleet_setup`; branch `codex/fleet-trusted-source-setup`.
Mandate revision: `owner-2026-11-13-source-granted-setup`.
Plan: [granted-source-fleet-setup](milestone-plan.json), MASK-0153 AC1–AC3.
Baseline: `165ca56`; claim: `4f0bf7a`.
Implementation candidate: `b86691fc917681f8c2d92dfc34eada7c6c4b98f6`.

The owner authorized existing device source, scope and upgrade grants to cover
controller-reviewed exact setup/native-role repairs, followed by coordinator
publication and live fleet rollout. This leaf changed MASK only, without
AgentSkills edits, live fleet mutations, grants or push.

## Result and verification

AC1: Authenticated exact candidate inspection precedes approval and reports
cache/store preparation plus script/package/input/interpreter fingerprints,
native roles and backup/replacement effects. Signed apply binds the task digest,
recomputes it locally and uses ordinary setup staging, validation and journals.

AC2: Per-coordinate/agent producer checks preserve layered ownership. Missing or
tampered task, signatures, expiry, invalid/stale inputs, changed role destinations,
source identity and scope/action checks refuse. Replacement backups retain prior
bytes; ordinary staged-journal rollback restores them. Failed/launched setup
never silently replays. Canonical Git controls and unrelated staging stay guarded.

AC3: Fleet guides, CLI wire contract and RFC-MASK-0012 record the amendment;
historical acceptance remains intact.

Completed commands and results:

```text
python3 -B scripts/run_tests.py -j 6 -k tests.test_fleet_ -k tests.test_upgrade_readiness -k tests.test_setup --slowest 5
82 tests / 15 classes; 0 skipped; 0 failed; 88 seconds.
python3 -B scripts/run_tests.py -j 4 -k tests.test_fleet_setup --slowest 3
9 passed; 0 skipped/failed; 24 seconds, final source candidate.
python3 -B -m unittest tests.test_fleet_setup.FleetSetupTests.test_interrupted_replacement_rolls_back_from_the_ordinary_setup_journal tests.test_fleet_setup.FleetSetupTests.test_source_scope_action_and_signed_task_authority_remain_required
2 passed; 16 seconds (one added case, one updated case; 10 distinct new setup cases).
python3 -B scripts/verify_documentation.py --root . --agent-skills ../AgentSkills
26 RFCs, 153 cards; 0 structural violations.
git diff --check
Pass. Normal commit hook: BetterLeaks 1.9.0, zero findings.
```

The broad pass preceded the last narrow producer-coordinate/concurrent-role
checks; final-source focused setup checks exercised those changes. Subsequent
test-only additions passed without source changes. Early failures exposed and
corrected per-device preview lock contention and device-wide generation hashing;
the canonical multi-scope test then passed. Other early failures were fixture
policy shapes and imported test-class duplication, both corrected. No known
product failures remain.

## Changed paths and self-review

Source: `mask_fleet_maintenance.py`, `mask_rpc.py`, `mask_lifecycle.py`,
`mask_present.py`; tests: `tests/test_fleet_setup.py`.
Docs: `docs/architecture/cli-contract.md`, `docs/guides/fleet-enrollment.md`,
`docs/guides/fleet-rollouts.md`,
`docs/rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md`.
Bookkeeping: MASK-0153 and this plan’s `milestone-plan.json`, `source.json` and checkpoint.

Self-review covered signed authority, selected-scope task hashing, exact cache
preparation, actual setup/asset producer coordinates, unchanged subscriptions,
setup journal/no-replay behavior, backups, Git propagation and final readiness.
No independent or attended acceptance was required by the assigned card.
Evidence is macOS subprocess/loopback fixture transport with disposable local bare
remotes; new native SSH/Windows/agent-loading evidence was not claimed.

## Ownership, command state and continuation

The leaf was the sole repository writer; coordinator owns publication and live
rollout after handoff. All task-owned commands are finished. No test subprocess,
server, descendant writer or protected review candidate remains active. Fixture
roots were removed by test cleanup. Runtime selection, checkpoint, acceptance
and logs remain in ignored `.mask/sessions/mask-0153/`.

Next: coordinator inspect/integrate onto `main`, push under the owner mandate,
update all four enrolled MASK program checkouts, then refresh and approve the
exact fleet skill task. Preserve dirty/diverged-control, detached/canonical,
local-drift and source blockers. Record live outcomes separately. Publication and
live fleet outcomes remain the coordinator’s pending obligations beyond this
completed engineering milestone.
