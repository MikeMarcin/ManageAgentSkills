---
schema: "implement-rfc.card.v1"
id: "MASK-0113"
title: "Verify and close RFC-MASK-0022"
status: "Backlog"
rfcs: ["RFC-MASK-0022"]
depends_on: []
closeout_for: ["RFC-MASK-0022"]
metadata: {"closeout": true, "reserve_for": "rfc-mask-0022-transport-neutral-tap-identity"}
---

# MASK-0113: Verify and close RFC-MASK-0022

Governing RFC: [RFC-MASK-0022](../../rfcs/RFC-MASK-0022-transport-neutral-tap-identity.md). The ID was reserved at `fb4728a`. The RFC is Implementing: the owner directed implementation on 2026-09-16, inline and without separate implementation cards.

## Objective and owned paths

Check every acceptance criterion against direct evidence. Record the real RFC_BASE_SHA before any source implementation, plus the actual implementation commits. Reuse focused results that have not changed. Leave the owner dogfood row (AC08) open until both machines' transcripts are recorded. Passing fixtures do not prove AC08.

Own only:
- `docs/rfcs/RFC-MASK-0022-transport-neutral-tap-identity.md`
- this closeout card
- the public contract docs the RFC changes

Coordinate shared files with the integrator.

## Acceptance and focused verification

- RFC-MASK-0022-AC01: Forge spellings normalize to one identity, and a declaration in any spelling ensures on machines approved with any other spelling.
- RFC-MASK-0022-AC02: Non-forge hosts stay strict. `forge_hosts` is a machine-only opt-in. `/~/`, a non-`git` user and a non-default port stay strict.
- RFC-MASK-0022-AC03: Derived transport follows the consumer origin, then the hint, then `gh`, then a noninteractive probe, and reports the chosen transport.
- RFC-MASK-0022-AC04: Pinning is explicit, machine-local and identity-checked.
- RFC-MASK-0022-AC05: Pre-RFC files and machines keep working, and `doctor --migrate` canonicalizes config and state recoverably.
- RFC-MASK-0022-AC06: Rewrite, redirect, credential and content-integrity refusals are unchanged.
- RFC-MASK-0022-AC07: Help, contract, schema, the documentation verifier and the full suite are truthful and green.
- RFC-MASK-0022-AC08: The owner dogfood on JaegAW and on an SSH-approved machine succeeds with no hand edits to `MASK_HOME`.

Proposed direct checks (not executed at filing):

- `python -B scripts/verify_documentation.py --root .`
- `python -B -m unittest`
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC, this card and the current source before editing. Use temporary fixture roots and local bare remotes. Preserve unrelated changes and commit explicit paths. Never edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: `754b722` (the last revision before any RFC-MASK-0022 source change).

Implementation revisions: `0726449` (identity, derived transport, pinning, fixture tests), `413ad87` (catalog canonicalization, contract, guides, help).

Planned cards: none; implemented directly at the owner's direction.

Cross-repository handoff: BetterPullReview `.mask.json` and `.mask.lock.json` may be relocked to the canonical spelling after the RFC lands. That is the owner's consumer change, not a MASK change.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0022-AC01 | `python3 -B scripts/run_tests.py -k test_tap_identity` (Linux/WSL2, subprocess CLI against `tests.forge_support`'s network-free forge): `Normalizer.test_forge_spellings_fold_to_one_https_identity`; `OneIdentity.test_every_committed_spelling_meets_every_approved_spelling` deploys each of 4 committed spellings on machines approved with each of 4 typed spellings (16 pairs), `ensure` exit 0 and both files byte-identical; `tests.test_sources` asserts the forge equality | Pass | `0726449` |
| RFC-MASK-0022-AC02 | Same run: `Normalizer.test_other_shapes_and_other_hosts_stay_strict`, `test_a_machine_opts_a_host_in_and_a_project_file_cannot`; `StrictElsewhere` refuses `source.identity_mismatch` on `example.test` until `config set --forge-host`. **Deviation:** `ssh://git@H/~/P` folds to the forge identity instead of staying strict, because AC05 requires it (RFC, Implementation notes) | Pass with recorded deviation | `0726449` |
| RFC-MASK-0022-AC03 | Same run, `TransportByConvention`: project follows `origin` (both schemes); personal scope uses `gh`, then the typed URL, then the probe, and a proven transport then outranks `gh`; a denied transport falls back, is reported in text and `tried`, and is remembered; an older catalog never contacts the `/~/` URI; `source show --json` reports `transport`, `transport_policy`, `chosen_by` | Pass on the fixture forge; no real forge contacted | `0726449` |
| RFC-MASK-0022-AC04 | Same run, `Pinning`: `--pin-transport` and `tap transport NAME URL` try nothing else; another identity refuses without effect; `--derive` unpins; no transport word in either project file | Pass | `0726449` |
| RFC-MASK-0022-AC05 | Same run: `OneIdentity` (pre-RFC HTTPS and `/~/` files verify their recorded digests and stay byte-identical; a quiet `upgrade` writes nothing; the next writing `upgrade`/`install` records the canonical spelling with unchanged digests); `OlderMachine` (doctor reports, `--migrate --dry-run` previews, `--expect-plan-hash` guards, one write converts the catalog). **Deviation:** the catalog only is converted, atomically and without a journal, so the crash-at-each-checkpoint clause has nothing to exercise (RFC, Implementation notes) | Pass with recorded deviation | `413ad87` |
| RFC-MASK-0022-AC06 | Same run, `Boundaries`: an `insteadOf` rewrite to another repository refuses `source.identity_mismatch` before any contact, one inside the identity is allowed; credential URL and effective redirect policy refuse; `Normalizer.test_every_derived_transport_is_a_spelling_of_the_tap_identity`. Commit and payload-digest refusals are unchanged code, covered by `tests.test_artifacts` and `tests.test_locks` in the full run | Pass | `0726449` |
| RFC-MASK-0022-AC07 | `python3 -B scripts/run_tests.py`: 484 tests, 0 failed. `python3 -B scripts/verify_documentation.py --root .` (skill scripts from the store on PYTHONPATH): 22 RFCs, 113 cards, 0 structural violations. Help, README, sources guide, CLI contract and `machine-v3.schema.json` updated | Pass on Linux/WSL2 | `413ad87` |
| RFC-MASK-0022-AC08 | JaegAW, no hand edits: this repository commits the HTTPS spelling and the machine catalog still records `ssh://git@github.com/~/MikeMarcin/AgentSkills.git`; `mask ensure --dry-run` no longer refuses `source.identity_mismatch` and reaches the `implement-rfc` setup consent step; `mask doctor` reports `migration.identity_canonicalization`; BetterPullReview (SSH spelling) reports ready. Not yet run: a real `ensure` to exit 0 here (needs the owner's interactive setup consent), and anything on the SSH-approved machine | **Open** | `413ad87` |

Closeout review runtime: not run. A skipped required native or owner check leaves its criterion open.
