---
schema: "implement-rfc.card.v1"
id: "MASK-0091"
title: "Qualify the ordinary CLI and replace the long getting-started guide"
status: "Done"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0084", "MASK-0085", "MASK-0086", "MASK-0087"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "native-human-journeys-and-readme"}
acceptance: [{"criterion":"RFC-MASK-0018-AC07","outcome":"pass","revision":"6dcd5a4c57b590bb511e778aa4eae40830055735","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_readme_journeys (macOS, 4 tests OK; Windows via py -3, 3 OK + pty skip): the short README's everyday recipes run as written through the launcher `self install` wrote and the plain entrypoint, with no --json, plan hash, registration chore or helper script; docs/guides/* keep the advanced material. Independent review found the dropped mkdir -p line (fixed in 6dcd5a4; literal chain rerun from an empty HOME)"}},{"criterion":"RFC-MASK-0018-AC08","outcome":"pass","revision":"a85651002f3dbf2b9a94c45a2c0e6564771b4b09","evidence":{"kind":"observation","detail":"macOS 26.6.2/Python 3.14.7 and Windows 11 10.0.26200/Windows Python 3.14.7 (ExampleWinHost, disposable clone) ran the public task/human-output/baseline/launcher suites; Windows console yes/no confirmation recorded as a bounded ConPTY interaction (exit 0 with link, exit 4 declined without link); macOS pty yes/no/pipe; see docs/development/corrective-baseline.md 'Native lanes'. Helpers never inject --json or prepare the behavior under test. Host loading remains not verified"}}]
---

# MASK-0091: Qualify the ordinary CLI and replace the long getting-started guide

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

README.md, current CLI/test-boundary instructions, public native macOS/Windows tests, launcher checks, and compact acceptance records.

## Bounded work

Replay the proposed everyday commands from a fresh project and personal home through actual CLI invocations without --json. Exercise one real native terminal consent/decline path per OS plus automated text/pipe/JSON coverage. Replace the current everyday guide with a short task guide only when it works; move advanced material to focused references, retaining truthful release/feature limits.

## Acceptance

The human scenario helper does not append --json or pre-register/render. README steps are executable and use no manual hashes. Both native lanes report actual runtime/filesystem/terminal boundaries; absent native evidence keeps this card open. No mandatory paid model call or full historical matrix is introduced.

Criterion coverage: RFC-MASK-0018-AC07, RFC-MASK-0018-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
