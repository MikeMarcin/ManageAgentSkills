# Draft structural checks

Checks rerun 2026-10-03 against the shortened version 1. These are authoring checks, not
implementation acceptance evidence.

## Offline plan validation

```sh
python3 ../AgentSkills/skills/implement-rfc/examples/milestone-plans/validate.py docs/rfcs/drafts/upgrade-auto-commit/milestone-plan.json
python3 ../AgentSkills/skills/implement-rfc/examples/milestone-plans/validate.py docs/rfcs/drafts/upgrade-auto-commit/milestone-plan.json --render
```

Result: exit 0, “Structurally valid; references and semantic coverage unchecked.”
The renderer generated MILESTONES.md from the exact final JSON. The portable schema
is copied unchanged from the discovered implement-rfc package.

## Pack checks

Local read-only checks verify Markdown file targets; JSON-valued RFC/card
frontmatter; unique provisional IDs; Backlog card status; exactly one closeout for
the proposed RFC; dependency and plan references; one authoritative definition
for each AC01–AC07; closeout table coverage; source-schema equality; and generated
view equality. Result: passed, 3 provisional documents, 7 unique acceptance
criteria, 31 local Markdown links; schema and generated view match.

Repository gate `python3 scripts/verify_documentation.py --root .`: exit 0,
23 live RFCs, 128 live cards, 0 structural violations. Drafts are outside this
gate's live top-level RFC and issue-board scan.

`git diff --check`: exit 0. A separate check of newly authored text verifies no
trailing whitespace, CR line endings or missing final newlines. The existing
dirty `.gitignore`, `.mask.json` and `.mask.lock.json` remain outside this draft.

## Limits

Live selectors are not adopted or bound. Structural success does not settle
material proposals D4–D7, confirm the whole design, prove semantic acceptance,
establish implementation eligibility or demonstrate command behavior. No runtime
tests were run for this documentation-only draft. No baseline, implementation
revision, source acceptance or native-platform result is claimed.
