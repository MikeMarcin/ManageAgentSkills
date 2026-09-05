---
id: MASK-0006
title: Implement serialized journaled symlink effects
status: Backlog
rfc: RFC-MASK-0002
depends_on: ["MASK-0005"]
---

# MASK-0006: Implement serialized journaled symlink effects

## Objective and owned paths

Own filesystem executor, OS lock, atomic JSON writes, pending intent and `tests/test_reconcile_apply.py`.

## Bounded work

Apply only revalidated actions under one local writer lock. Integrate prospective manifest --apply into the same path. Preserve unknown content, journal before effects and attempt narrow safe rollback.

## Acceptance

Correct links converge; stale owned links remove only when raw value/type agrees; manifests stay unchanged on preflight refusal; injected late failures are nonzero and truthfully reported.

## Focused verification

`python -m unittest tests.test_reconcile_apply tests.test_manifest_registry`; actual temporary symlinks, not only mocked calls.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
