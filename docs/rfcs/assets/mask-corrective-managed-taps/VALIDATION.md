# Actual pack checks

## Checks run in this environment

Environment: Windows 11, Python 3.14.6, Git for Windows. These are pack checks,
not native qualification, not implementation of the RFC and not a migration of
any machine.

| Check | Actual result |
|---|---|
| `python -B tools/validate_pack.py --skip-manifest` | Passed apart from the expected missing `VALIDATION.md` link before this file existed: one proposed RFC, nine provisional cards, eight criteria, one closeout, criterion coverage lines match `issue-plan.json`, milestone scope equals the card plan, machine v3 schema has no live source block, every relative Markdown link resolves |
| `python -B implement-rfc/examples/milestone-plans/validate.py milestone-plan.json` | `Structurally valid; references and semantic coverage unchecked.` `MILESTONES.md` is the `--render` output of the same command |
| `python -B implement-rfc/scripts/milestone_plan.py discover --repo-root . --source-root <pack> --json` | `state: found`, `plan_id: tap-only-deployment`, `structural: valid`, seven milestones |
| `python -B implement-rfc/scripts/milestone_plan.py check --repo-root . --source-root <pack> --plan milestone-plan.json --json` | `structural: valid`, `semantic_coverage: unknown` |
| Card front matter against the installed `issue-card.schema.json` grammar | All nine cards parse with one JSON value per line; exactly one is Ready with no dependencies; the closeout's `closeout_for` is a subset of `rfcs` |

The final manifest is generated after this record is written, and
`tools/validate_pack.py` is run again in full so the manifest binds every
deliverable file except itself.

## Baseline observation

The observed source facts in `SOURCE_BASIS.md` were read directly from the
checkout at `d3e417478809e096be9cff155e38c7620d14ee71`. The owner's machine
configuration was read from `~/.mask/config.json` and `~/.mask/state.json`. No
MASK command was run against that configuration, no fixture reproduction was
executed, and no consumer was created or migrated while authoring this pack.

## Not performed or claimed

No product changes, live ID reservation (performed separately by the integrator
at import), native macOS or Windows qualification, real-package qualifier run,
owner machine migration, credential or permission change, Git publication or
disk-usage measurement. Pack integrity is not a PASS on any acceptance
criterion.
