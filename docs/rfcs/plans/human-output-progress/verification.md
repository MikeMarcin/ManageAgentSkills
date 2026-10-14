# Human output and progress verification

MASK-0121, direct source work in the existing checkouts. No subagents or
independent review; acceptance is the primary engineer's judgment.

## Accepted behavior

- AC1: Canonical implement-rfc README, personal setup, role adoption and coordinator
  guidance use current commands and combined task approval. The root AgentSkills
  onboarding and public example runner agree. The intentional advertised old-program
  compatibility branch remains tested. AgentSkills handoff:
  `fbd909de1fad209dab8f2fcec6baca9b27ce0bfd`.
- AC2: Reviews and previews group ordinary changes by location; identical setup code
  is disclosed once with its fingerprint, interpreter, recipients and exact role
  targets. Explicit backup/replacement paths remain visible. Internal store paths
  and stale pre-setup role lists are suppressed. Multiple backup sets are summarized.
  Setup results distinguish published, incomplete and unstarted actions.
- AC3: Terminal tasks flush phase messages before slow work, pause during review,
  resume immediately after approval, and report elapsed activity during long phases.
  Setup names its consumer; progress stops on completion or failure. Terminal color
  respects NO_COLOR and TERM=dumb. Pipes stay plain; JSON stays one result document,
  including when stdout/stderr are attached to a real pseudoterminal.
- AC4: Publication/rollback failures retain both typed causes and the pending
  journal. Unconfirmed action effects use the existing failed status with an
  additional effects=unknown fact, retaining the result schema. Setup termination
  uncertainty is distinguished from a staged publication failure. Workspace
  conflicts now identify the root and changed observation fields.
- AC5: Focused renderer, lifecycle, consent, launcher, re-exec and canonical skill
  checks pass. Runtime and documentation checks are described below. The runtime
  module list includes mask_progress.py for candidate validation and clone fixtures.

## Checks and corrections

Detailed local logs are in `.mask/sessions/human-output-progress/`:

- `renderers.log`: 9 checks passed.
- `public-checks.log`: 36 checks, one failure in the new timing assertion. The
  transcript proved live progress at 18/28 seconds; its exact-10-second test
  expectation was wrong. Heartbeat scheduling was tightened to the current phase,
  and the assertion now accepts observed elapsed time.
- `progress-fixed.log`: 20 passing checks, including imported lifecycle classes.
  The test module imports were then narrowed to avoid duplicate suite collection.
- `final-progress.log`: all 7 dedicated progress/presentation cases pass, including
  a public upgrade whose setup waits until the test observes a live heartbeat.
- `json-terminal.log`: the additional public JSON-on-terminal case passes.
- `final-presentation.log`: 14 renderer, help and README checks pass.
- `final-failure-schema.log`: 5 checks pass, including public injected forward and
  rollback failures and action statuses constrained to the existing JSON schema.
- `launcher-refresh.log`: 2 checks pass: installed launcher forwarding and program
  update/re-execution before installation, with the new runtime module included.
- `upstream-public.log`: the initial canonical skill test failed because the
  migrated tap fixture omitted its authoring checkout. After restoring that fixture
  option, `upstream-public-fixed.log` passes the full two-consumer source/installed
  profile and development-link scenario.
- `upstream-preflight.log`: 12 compatibility/preflight checks pass.
- `upstream-validation.log` exposed a stale portable-source manifest, including
  earlier source changes. The supported source-only manifest writer refreshed it;
  `upstream-validation-fixed.log` passes. No consumer adapters were rendered.
- Documentation gates pass: MASK 23 RFCs/121 cards; AgentSkills 14 RFCs/90 cards;
  zero structural violations. Changed Python syntax and git diff whitespace pass.

These are focused checks, not a claim that the complete repository test suite
was rerun. The terminal journey ran on macOS; native Windows was not exercised.
The simplification pass consolidated setup disclosure grouping and kept color and
progress at the presentation boundary, outside task decisions and result JSON.

## Pasted failure and remaining live state

Read-only recovery inspection found a staged implement-rfc publication for
ExampleNotes in transaction `24e6c819-77a1-4099-86b2-c06624bf760c`, following the four
published setup groups shown in the user's transcript. The old failure path did
not preserve its original cause, so that cause cannot be established afterward.
The retained workspace observations currently differ at ExampleReview's HEAD
and at this MASK checkout's HEAD (which this source task has advanced). This is
current drift, not proof of the original failure. The journal and live deployments
were not modified, completed or rolled back by this task.

The new source makes future failures actionable; it does not claim to repair this
existing live recovery. Installed skill payloads were not migrated. Canonical
skill instructions reach a locked installation through a later successful upgrade.
No push/publication occurred; unrelated lockfile edits in both repositories remain
preserved.
