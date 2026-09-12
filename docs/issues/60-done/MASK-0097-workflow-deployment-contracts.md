---
schema: "implement-rfc.card.v1"
id: "MASK-0097"
title: "Publish workflow paths and repair retired generated files"
status: "Done"
rfcs: ["RFC-MASK-0019"]
depends_on: []
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"973eede8fb9b4d1289fc684deac15b3e6c0fdb13","evidence":{"kind":"observation","detail":"Public CLI tests verify capabilities paths and setup-request paths; canonical AgentSkills renderer consumes advertised future paths and real capabilities. Real package qualifier 44/44 steps."}},{"criterion":"AC2","outcome":"pass","revision":"973eede8fb9b4d1289fc684deac15b3e6c0fdb13","evidence":{"kind":"observation","detail":"87 focused regression tests pass on native macOS, including explicit repair backup/removal, normal/check/dry-run preservation, unsafe paths, active fallback, setup-time/external edits and crash complete/rollback. Exact CRLF backups preserved."}},{"criterion":"AC3","outcome":"pass","revision":"973eede8fb9b4d1289fc684deac15b3e6c0fdb13","evidence":{"kind":"observation","detail":"Output-identical helper edit with exact prior contract_sha256/role_inputs_sha256 passes without setup or lock rewrite; changed consumer inputs, role bytes or hash pair fail. Actual renderer source fingerprint changes bytes, so no false compatibility assertion was published."}}]
---

# MASK-0097

Owner-authorized direct implementation, September 12, 2026. Baseline:
`832380e051884634045a16d934f89b866da05a95`, with existing uncommitted lock
relocation edits preserved and incorporated. No adopted milestone plan exists.

One bounded milestone covers the owner's three deployment problems:

- AC1: setup requests and capabilities publish MASK-owned lock paths.
- AC2: readiness reports retired files; only explicit repair removes bounded
  files through recoverable transactions with durable backups. Normal commands,
  checks and previews preserve them, as do unsafe paths and active fallback locks.
- AC3: explicit package compatibility assertions admit prior input fingerprints
  without execution, retaining consumer-input and exact role-output verification.

Owned scope: workflow/setup/capability/repair transaction code, focused subprocess
tests and current contract documentation. AgentSkills integration is a separate
canonical-source handoff; no unrelated consumer migration or push. Existing
RFC-MASK-0019 host-loading obligations remain open.

## Verified outcome

Implementation: `973eede8fb9b4d1289fc684deac15b3e6c0fdb13`.
Canonical AgentSkills adoption: `df308c56d6d55a91fd5ae5f1df9ee5aa0ca69212`,
closed out by ASK-0074 at `c8734bade8cc98578baa04ddbe1cf49d7dc1217e`.

Native macOS 26.6.2 / Python 3.14.7: the combined command
`python3 -B -m unittest tests.test_repair tests.test_setup tests.test_workflow_roles tests.test_workflow_deployment tests.test_recovery tests.test_ensure tests.test_human_output`
passed 87 tests. The new deployment suite contributes 11 subprocess cases:
request/capability paths, compatible exact prior hashes without execution,
consumer-input/output tamper rejection, normal/check/preview preservation,
backups with exact CRLF bytes, idempotent cleanup, retained active fallback,
cleanup after successful setup, unsafe/malformed entries, complete/rollback
recovery, external edits and setup-time changes. Cleanup stays advisory when an
entry cannot safely retire, and an active declared input is never removed.

`scripts/qualify_real_package.py` passed 44/44 public CLI steps with two disposable
contexts and a fresh clone, using the upstream revision above and this exact
MASK working candidate before its source commit. The report at
`/tmp/mask-0097-real-package-report.json` records the earlier HEAD plus the dirty
candidate; the source implementation revision above identifies the tested bytes.
Disposable clones were removed after verification. Real-capability discovery was
also checked by the upstream renderer against the deployed disposable beta roles.
The documentation gate passes: 19 RFCs, 97 cards, zero structural violations.

Compatibility assertions intentionally require both prior descriptor and package-
input hashes because declaring compatibility itself changes the descriptor hash.
No assertion was added to implement-rfc: both real consumer comparisons found
16/16 outputs change in their embedded full-renderer-source fingerprint. Their
remaining role bytes match, but that does not justify a byte-equivalence claim.
The renderer adoption needs one setup; later MASK-only path moves need no skill
edit. No live consumer cleanup, setup, approval grant or push was performed.
Windows and fresh host loading were not requalified by this follow-up; prior
RFC-MASK-0019 obligations remain unchanged. Task writers and commands are stopped.
