---
schema: "implement-rfc.card.v1"
id: "MASK-0041"
title: "Implement portable personal profile export and import"
status: "Backlog"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0069", "MASK-0070"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "portable", "stage": "C — portable composition", "provisional_id": false}
---

# MASK-0041: Implement portable personal profile export and import

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Export local or explicit effective selections plus exact locks with no local registry/secrets. Preserve all-agent defaults and optional freeze-agents. Import via incremental or explicit replacement semantics and one validated apply path; test two machines with different paths.

Own only: `mask_profiles.py (new)`, `mask.py`, `tests/test_profiles.py (new)`, bounded planner/pinned-observation/journal integration in `mask_fs.py` and `mask_pinned.py`, runtime inventory in `mask_install.py`/`tests/test_launcher.py`, affected typed schema definitions and current README/CLI documentation. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC01: Export/import round-trips selections and exact content locks between different machine/home/source paths without including credentials, registry identities, journals or launchers.
- RFC-MASK-0010-AC02: Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- RFC-MASK-0010-AC05: One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_profiles tests.test_user_scope

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.

## Planned bounded decisions

Dependencies remain open until MASK-0069/0070 finish. No implementation or portable/native acceptance is asserted by this plan. RFC_BASE_SHA remains the imported closeout anchor 9dc90df45febf2a6e048ace60a4ac959807aaaf6.

Use the specified user export/import and profile inspect syntax. Export publishes only bounded selection.json/selection.lock.json and optional human README into an explicitly absent output directory through native no-replace publication. Inspection validates the portable pair without requiring a machine config, local source approval or cache. Do not serialize registry, physical home/source/cache paths, credentials or local compatibility authority. Plain exports preserve all; explicit effective/frozen exports describe the semantic change, and package rows remain exact while the declaration digest changes when required.

Incremental import changes only the local user contribution and preserves positive target intent and unrelated bindings; replace is explicit local-contribution replacement. Equal artifact/repository authority follows RFC-0009 union, not last-arrival precedence or ordinary explicit-list denial. If two conditions/constraints cannot be represented faithfully in one binding, return a precise conflict rather than broadening them silently. Subscriptions and bundle ownership stay in later cards.

One import-and-apply command can register a selected existing personal home, prepare available exact artifacts outside the writer, then atomically reconcile declaration/lock/owned links/state under the ordinary journal. Observe exact prior absence for new user controls and registration, as well as config/source/policy/home/root identities. Collisions preserve all before bytes. Recovery must restore exact absence/presence or complete the frozen pair without repeating a merge. Reuse --user-home semantics when an explicit test/owner home is needed; never change HOME to redirect the process.

The two-machine fixture must use public source approval/migration/preparation, different authoring/cache/MASK_HOME/user roots and one credential-free portable repository identity. Do not make the test pass by editing MASK's internal state/cache or by rewriting repository identity with insteadOf. Approved local authoring clones with the same HTTPS origin can prepare exact raw artifacts through public project migration before importing into a new user scope; unavailable exact content remains an honest prerequisite. Native personal import acceptance remains open until the later native profile milestone.
