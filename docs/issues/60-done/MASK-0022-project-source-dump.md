---
schema: implement-rfc.card.v1
id: MASK-0022
title: Add a project source dump script
status: "Done"
rfcs: []
depends_on: []
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"8963f9cf1523f4329a3756a2d996ed29b58e11f5","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_project_source_dump: all 6 tests pass, including working-tree discovery, classifications, manifest ordering, and embedded Markdown fences."}},{"criterion":"AC2","outcome":"pass","revision":"8963f9cf1523f4329a3756a2d996ed29b58e11f5","evidence":{"kind":"observation","detail":"Fixture subprocess checks verify exclusions even with --include-generated, including file/directory/broken symlinks. Real checkout manifest contains MASK sources and portable context, excludes local agent directories, retired/generated MASK data, output, .DS_Store, and RFC archive."}},{"criterion":"AC3","outcome":"pass","revision":"8963f9cf1523f4329a3756a2d996ed29b58e11f5","evidence":{"kind":"observation","detail":"All 6 subprocess tests pass for default/custom/absolute output, stdout, reruns, invalid roots and invalid text. Invoked the absolute script from /tmp on macOS with no root/output overrides: default artifact contains 81 files, 394679 bytes. README documents options; git diff --check passes; python3 -B scripts/verify_documentation.py --root . reports 5 RFCs, 22 cards, 0 structural violations. TemporaryDirectory fixtures cleaned automatically. Script manually reviewed for straightforward control flow and shared extension/language mapping."}}]
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
