# Station takeover amendment: incidental bytecode

Mandate `station-local-takeover-20260929-v2`; assignment `/root/station_takeover`.
MASK baseline aa72588162fb9e9a0b92a32059e6dd3c674c4665. AgentSkills owns the station
lifecycle; this repository owns bytecode verification. No native stops or deployment.
Current frontier: claim MASK-0127, correct common verification, run focused public
imports/recovery/setup checks, commit explicit paths. Unrelated `.mask.lock.json` is
preserved. No background commands or additional agents.

Implementation: common no-follow source verification preserves bounded, flat,
unlinked interpreter caches and numeric atomic-write temporaries. Source and cache
entry capacity are bounded separately by a derived combined allowance; portable
inventory keys use PurePosixPath. Shipped bytecode is explicitly rejected by artifact
manifest validation. No verification path deletes interpreter caches.

Verification: focused artifacts, normal linked import/preview consent, cache-preserving
status/repair and recovery, and shipped-bytecode rejection: 22 passing cases in the
final focused run; its added near-capacity fixture initially overfilled the cache
budget and was corrected, then passed separately (1 test). Prior broad setup run:
43 passes with one shipped-cache rejection regression, corrected and narrowly rerun.
Structure gate: 23 RFCs / 127 cards, zero violations. Concise changed-code review
checked portable keys, source identity, bounds, cache-only races and explicit rejection.

Root's read-only actual environment observations on 2026-09-29: normal `python3 mask.py
status --project ROOT --check --json` for BetterPullReview and AgentSkills both exit 0,
`ready_pinned`, zero issues. The installed implement-rfc artifact's 101 Python sources
and 5 bytecode files have identical before/after SHA-256 maps. Installed workflow
preflight now reports ready with the configured project and personal rfc-implementer
routes; actual native role loading remains not_verified. No deployment or station
stop was performed. No live native Windows evidence is claimed.

Paired final AgentSkills engineering handoff:
bf257dabf48dde0527dc8e92e012095d71e7126c; ASK-0091 acceptance
bb82eb8c32ee14a80ef9cdbcfa9d443690c9be58. The coordinator's BetterPullReview
read-only dev-link preview has no blockers and exactly two skill links plus state
record; actual deployment and new-chat host loading remain unperformed. Native
owner-proxy stop could not be qualified on this host (absent existing control socket).
All MASK task commands exited; no temporary station process, server or internal-state
repair remains. The only dirty path here is the pre-existing `.mask.lock.json`.
