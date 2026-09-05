---
schema: implement-rfc.card.v1
id: MASK-0022
title: Add a project source dump script
status: "In Progress"
rfcs: []
depends_on: []
---

User-requested standalone tooling change inspired by SampleReview's
`scripts/make_project_source_dumps.py`. This card is its closeout anchor;
no live RFC behavior changes.

Owned paths: `scripts/make_project_source_dumps.py`,
`tests/test_project_source_dump.py`, `README.md`, `.gitignore`, and this card.

Acceptance:
- AC1: The standard-library Python CLI produces one Markdown dump of MASK
  source, schemas, tests, docs, and portable project context, with an ordered
  manifest, classifications, and fences that contain embedded backticks.
- AC2: Default discovery excludes caches, virtual environments, generated
  output, local MASK state/retired copies, linked skills, and binary artifacts.
  It includes working-tree edits and new source files, without following links.
- AC3: Default output, custom root/output, stdout, generated-directory opt-in,
  repeated runs, and invalid-root errors work through subprocess fixture checks.
  Document usage and smoke-test the real checkout on macOS.

Verification: focused disposable-fixture tests, real-checkout dump inspection,
and the repository documentation structure gate.
