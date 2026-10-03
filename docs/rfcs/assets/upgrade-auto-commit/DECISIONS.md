# Design record

Version 1, shortened on 2026-10-03 without changing proposed behavior.
[Original request and answers](originals/USER_REQUEST.md) preserve provenance.

| Decision | RFC reference | Status / answer | Consequence / dependencies |
|---|---|---|---|
| D1 Upgrade option | R1 / AC01 | Settled: owner requested an option; `--commit` spelling confirmed | Default behavior preserved |
| D2 File set | R2 / AC02 | Settled: “Commit both when changed (Recommended)” | Coherent declaration/lock pair; depends on D1 |
| D3 Existing changes | R2 / AC02 | Settled: “Include existing MASK changes (Recommended)” | Full final controls, including partial staging; depends on D2 |
| D4 Scope | R3 / AC04, AC06 | Settled: one commit per selected project; personal skipped; personal-only flag invalid | Matches scope selectors; depends on D1–D3 |
| D5 Git boundaries | R2–R4 / AC02–AC04 | Settled: preserve unrelated staging, preflight eligibility, bind preview and revalidate | Isolate control commits; depends on D2–D4 |
| D6 Timing/failure | R5–R6 / AC05–AC06 | Settled: post-readiness commits; preserve applied effects and aggregate successes | Truthful partial results; depends on D4–D5 |
| D7 Configuration/output | R1, R4–R6 / AC01, AC03, AC05–AC06 | Settled: fixed message, normal Git configuration, no push, per-consumer outcomes | Bounded explicit interface; depends on D4–D6 |
| D8 Implementation mechanism | R2–R5 / AC02–AC05 | Explicitly deferred to engineering | Observable behavior required; depends on D5–D7 |

All decisions affect the RFC, implementation card and milestone. A later behavioral
change must update those artifacts and affected acceptance together.

Owner confirmation on 2026-10-03: “confirm go ahead” adopts D4–D7 exactly as
proposed. D1–D3 remain settled. Mandate `upgrade-auto-commit`, revision 2.
All seven criteria remain required; structural checks are not acceptance evidence.
Git/index internals remain the implementing engineer's responsibility.

Message customization, persistent defaults, direct bundle-command support, personal
commits and setup-output commits are excluded. Next action: authorized live adoption,
implementation and direct public CLI verification.
