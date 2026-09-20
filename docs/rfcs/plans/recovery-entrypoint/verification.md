# Recovery entrypoint verification

MASK-0122; direct execution in the existing checkout. No subagents or independent
review. Closeout review runtime: primary self-review with the code-simplifier
instructions; no delegated model runtime or host-loading claim.

## Accepted behavior

- AC1: Bare `recover` inspects without a mode flag or mutation. Blocked operations
  point to `repair`. Repair reviews interrupted setup at its recorded location,
  finishes validated publication or rolls back unvalidated publication, then ends
  that invocation. JSON and redirected callers need the exact preview hash;
  terminal callers review and answer the question. Advanced non-setup recovery
  retains explicit complete/rollback modes. Help and the command buckets document
  this boundary and its scope.
- AC2: Only frozen role-only setup publication can disregard HEAD/index movement.
  The before/after registries may differ only in generation and the setup skill's
  journaled role ownership. Links, selections, controls, development or program
  changes exclude the exception. Exact generation inputs, declaration/lock text,
  root and Git identities, authority, artifacts, destinations and registry state
  remain checked. Recovery may preserve regular bytecode-only cache directories
  while verifying every locked source byte; it never imports the package. Other
  extra content or links remain errors. Pre-review verification is observational.
- AC3: Public subprocess and real terminal fixtures prove completion, rollback,
  refusal, preview/hash approval and unchanged setup-launch counts. Existing
  recovery and artifact invariants remain covered by their retained suites.
- AC4: The reported live operation was completed through public repair with its
  reviewed hash. The installed launcher now runs `update` successfully. Exact
  postconditions and the limits below were recorded; no internal state was edited
  by hand and no package setup was rerun.

## Checks and corrections

Local logs are retained under `.mask/sessions/recovery-entrypoint/`:

- `public-recovery.log`: six new cases initially reached one fixture permission
  error when intentionally corrupting a read-only artifact. The fixture now makes
  its own file writable for that edit, restores its original mode before the CLI
  check, and restores the bytes afterward.
- `focused-tests.log`: 35 checks; all recovery and artifact checks passed. One
  existing human-output assertion expected the old link summary. It now checks
  the grouped summary introduced by MASK-0121.
- `final-focused-tests.log`: all 21 public recovery and human-output checks pass,
  including seven dedicated recovery cases. They cover unchanged controls
  committed with unrelated work, preserved bytecode, altered inputs and controls,
  edited roles/source, unknown artifact files, linked roles and bytecode, unchanged
  guards for non-setup journals, unvalidated rollback, decline and terminal consent.
- `final-guidance.log`: two focused checks pass after the final help wording and
  the assertion that blocked `update` directs the caller to `repair`.
- The retained four setup recovery and eleven artifact cases passed in the
  focused run. They were not rerun after presentation/documentation-only edits.
- Documentation validation reports 23 RFCs, 122 cards and zero structural
  violations. `git diff --check` passes.

The tests ran on macOS with disposable fixture roots and local bare remotes.
No full-suite, native Windows, power-loss durability or host-loading acceptance is
claimed. Direct workflow selection remains unchanged; installed readiness was
observed as incomplete at entry and does not prevent this source correction.

## Live recovery and update

Transaction `24e6c819-77a1-4099-86b2-c06624bf760c` contained staged implement-rfc
publication for PlaceOfMind. Its selected observations included eight consumers,
but its remaining effects were only 18 role entries, the role lock and matching
registry ownership in PlaceOfMind. There were no pending link, typed control,
selection or program changes. All 18 role files already matched the recorded
after-state before recovery.

Current recovery blockers were HEAD/index drift in the observed checkouts and
incidental Python caches in the locked artifact. The original publication failure
predates this correction and was not retained by the old error path; these later
blockers do not establish its original cause.

Read-only `repair --dry-run --json` produced the reviewed plan hash
`sha256:d28ada02cb95a4d24802a4b2ba71dbb3b5aafb5bc2918535388d0beebdad34ee`.
Applying that exact hash returned `ok: true`, `changed: true`, and
`transaction: committed`. Independent read-only comparison verified:

- the pending journal is absent;
- the registry text equals the journal's exact after-state;
- all 18 role files and the native role lock equal their recorded after-state;
- all ten previously observed bytecode files retain their exact hashes.

The installed launcher reports no pending recovery. Running its `update --json`
from AgentSkills succeeds and fetches the tap from
`6a59176a68ef4bd60b5b63321927c4c663cc4d81` to
`cd637fd9eceb41303fe82d8941574f8ab602773c`. Program self-update reports held because
this source correction was uncommitted at that moment; it preserves the checkout.
Runtime receipts are `live-preview-final.json`, `live-before-observation.json`,
`live-recovery.json`, `live-after-observation.json` and `live-update.json`.

Recovery did not resume the rest of the earlier multi-consumer upgrade, alter skill
versions, rerun setup, migrate installed skill instructions, push or publish.
Callers can run their next intended command now. This is recovery of the reported
operation, not a claim that every registered consumer is ready.
