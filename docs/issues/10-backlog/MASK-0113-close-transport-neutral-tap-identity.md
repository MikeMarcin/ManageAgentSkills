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

Governing RFC: [RFC-MASK-0022](../../rfcs/RFC-MASK-0022-transport-neutral-tap-identity.md). The ID was reserved at `fb4728a`. The RFC is Proposed. Implementation cards are allocated only after owner acceptance.

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

RFC_BASE_SHA: unrecorded until implementation starts.

Planned cards: unallocated.

Cross-repository handoff: BetterPullReview `.mask.json` and `.mask.lock.json` may be relocked to the canonical spelling after the RFC lands. That is the owner's consumer change, not a MASK change.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0022-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC05 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC06 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC07 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0022-AC08 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native or owner check leaves its criterion open.
