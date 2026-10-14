# Final public-source preparation evidence

The M3 record below preserves its original licensing wait and verification history.
The owner subsequently chose MIT; [M4 adoption](#m4-mit-adoption) supersedes that
wait. Native and post-visibility public CI boundaries remain open.

M3 / MASK-0141 and MASK-0142, mandate `public-prep-final-reconciliation-v1`,
coordinator-implementer recipe revision 2. This follows
[M2 verification](../rfcs/plans/public-source-preview/verification.md).
Accepted M2 input: `4ba72a7235d8a94d0d8cb386a672a51e671702bc`.
Metadata correction: `5648194410dbba068ec46b9929e9430e0a69c43c`.
CI fixture correction: `ce77dd95c4af947ac4a0c1a73e0e5db9045748ab`.
The accepted input remains an ancestor; production and workflow inputs are unchanged.

MASK-0133's historical acceptance changes only the Windows and Git Bash user
prefixes in AC4's evidence detail to EXAMPLE. Every other frontmatter field,
acceptance outcome/revision and original body byte remains unchanged; the appended
privacy note identifies this as a sanitized historical projection. Original paths
remain in history. This edit does not recertify or repeat the earlier Windows run.

## Private CI diagnosis and exact correction

[CI 38529937342](https://github.com/MikeMarcin/ManageAgentSkills/actions/runs/38529937342)
on `4ba72a7` reported 601 tests, 12 declared skips and four errors. All four fail
at consumer Git commits in RecoveryEntrypoint. PublicFixture configured the source
repository's author, but its consumer repository had no local author identity.
Configured or auto-detected host identity had hidden that fixture requirement.

An empty-profile clone with system/global Git config disabled passed the initial
local diagnostic because macOS Git could auto-detect an author. That unexpected
pass is retained. A strict isolated global `user.useConfigOnly=true` with no author
exposed exit 128: "Author identity unknown" and disabled email auto-detection.
The controlled baseline failed at the same consumer commit as CI.

At `ce77dd9`, RecoveryEntrypoint's setup calls the existing lifecycle setup and
configures local Fixture / fixture@example.invalid identity in its consumer Git
repository. AST comparison confirms all ten original methods, including seven
test methods, are unchanged. No assertion, skip or production behavior was removed.

Exact-candidate fresh-clone check:

```sh
python -B scripts/run_tests.py -j 4 -k tests.test_recovery_entrypoint --slowest 7
```

Seven tests, zero skips/failures, 13.363 seconds on macOS/Python 3.14.7. The profile
was empty; inherited Git/MASK/workflow/EMAIL variables were absent; system Git
config was disabled; strict isolated global config supplied no author. Only fixture
local identity allowed commits. All temporary roots were removed on completion.
The tested file SHA-256 is
`0cd9a53d4d906f16a960bada68fa0084731264e56f094c94339d3a81d834e2eb`.
Final GitHub CI remains a separate coordinator observation.

## Other verification and limitations

Documentation: 24 RFCs, 142 cards, zero structural violations; whitespace and
changed local links pass. AgentSkills's two real public MASK examples also pass;
only metadata and the isolated fixture setup changed afterward. M2's full local
600-case run and focused corrections retain their actual original failures, fixed
omissions and nine platform/dependency skips. The seven affected CI tests provide
new evidence; no unchanged full local rerun is claimed. Prior real bundle/import,
installed launcher and directory-rebind evidence is reused for unchanged inputs.

Exact source candidates pass Gitleaks 8.30.1 main-history, exported-tracked-tree and
new-commit-metadata scans using explicitly forced default rules, an empty ignore,
ignored allow comments, full redaction and archive/decoding traversal. Private final
records bind subsequent bookkeeping commits and remote main identities. Historical
blob/ZIP/metadata scans are reused for unchanged inputs. Scanner success does not
establish exhaustive absence of credentials or other private metadata.

The targeted current user-path scan retains immutable provenance metadata at
`docs/rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md` line 3 and
`docs/rfcs/assets/upgrade-auto-commit/DRAFT_CHECKS.md` lines 9 and 10. These are two
current tracked files, distinct from earlier metadata in history and archives.
Immutable packet bytes/history remain unchanged. Compatibility identifiers and
public repository identity remain literal.

MASK-0140 retains the unanswered owner license choice. No root LICENSE, visibility,
credential grant, real deployment or model experiment was added. Native roadmap
acceptance remains on its live cards. After both repositories become public, the
owner manually dispatches each Source checks workflow on main; visibility alone is
not a configured trigger. Private CI and local companion evidence do not certify
the post-switch public checkout/integration branch. The M3 handoff records actual
ordinary pushes, final remote identities, pending decisions and writer release.

## M4 MIT adoption

On 2026-10-14 the owner selected MIT for original code, skills and documentation
in both repositories. Mandate `public-prep-mit-adoption-v1` authorizes adoption
and ordinary main pushes. The [root MIT license](../../LICENSE) and
[README scope](../../README.md#license) implement that choice. This repository
contained no tracked LICENSE/NOTICE files to replace. Dependencies and approved
tap packages retain their own terms and provenance. AgentSkills preserves all
existing third-party notices and carries its original-contribution MIT notice
inside each independently distributed skill package.

Accepted input `3f6101d7edafa0da28a71c45c5e1670b764ddcf9` passed exact private CI
[38533348436](https://github.com/MikeMarcin/ManageAgentSkills/actions/runs/38533348436):
601 cases, 12 skips, zero failures. This documentation/license-only adoption
reuses that unchanged runtime evidence. Focused M4 checks and final source/push
identities are recorded with MASK-0140's closeout and the coordinator handoff.
Earlier M2/M3 pending-license statements remain historical observations.

The licensing wait is resolved. Visibility and private security-reporting activation
remain owner actions; after both repositories are public, manually dispatch both
Source checks workflows and confirm their public companion steps. Native and
attended roadmap acceptance remains on its live cards. The recorded consumer
adapter drift is separate from source acceptance and is not repaired by this work.

M4 license source candidate: `11c5109559f30cdcec229e036559f0a25d203d38`. The root license exactly matches the
reviewed standard MIT text with the repository-contributor copyright. Focused
documentation checks pass (24 RFCs / 142 cards); changed local Markdown links and
whitespace pass. Existing notice-file hashes match the accepted inputs. Outgoing
commit content, the exact tracked tree and new commit metadata report zero
Gitleaks findings with forced default rules, empty ignore and full redaction.
Final bookkeeping/push identities and scan receipts remain in the durable handoff.
