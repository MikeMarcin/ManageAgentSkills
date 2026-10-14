# MASK source preview preparation — M2

Assignment: public-source-preview/m2, mandate public-prep-mask-push-v2,
coordinator-implementer recipe revision 2. Sole MASK engineering writer;
implementation and self-review, no delegated or independent review. Baseline
`f49ac404bdb1366637841ee42e35cb34b13b6eaa`. Source candidate
`3aac8aeb06f5eb36518fffc07a53eae6f11ac7ae`; upstream AgentSkills input
`8c9c80f05e02e0cbaca56edfde5dab8859f2f932`. M3 owns final reconciliation and
license adoption after the existing owner choice. No visibility/access change,
real consumer migration, model experiment, force push or history rewrite.

## Recovery and output

MASK-0115 uses an explicit reviewed `register --rebind` step, followed by
`repair --all`. It requires the same canonical real directory and inode;
ordinary identity checks retain device-plus-inode equality. Existing approvals,
Git common-directory identities, installed integration records and matching
compatibility overrides follow the rebind; flags and grants are preserved.
Replacement directories, changed common roots, collisions, changed owned links
and stale review hashes refuse. The fixed-control journal supports inspected
completion/rollback without setup replay. Inode reuse is not proof of continuity;
the operator's explicit reviewed decision supplies the recovery authorization.
See [recovery](../../../guides/recovery.md#device-number-changes-after-restart).

Seven public subprocess cases pass: project/personal recovery, all-scope repair,
unregister, real root/common-directory replacement refusal, stale approval and
collision preservation, installed integration/override identity preservation,
interrupted control completion/rollback, terminal decline and one confirmation.
An actual installed macOS launcher additionally passed unapproved refusal,
reviewed rebind, repair-all, status check and unregister. All roots were disposable.
This is simulated device renumbering, not observation of a real reboot.

The four initial audit failures were corrected: launcher fixtures isolate
NO_COLOR; two old assertions now follow accepted MASK-0139 compact success and
mixed-failure output while preserving effect assertions; blocked generated-role
readiness names the missing roles and still prevents host launch.

## Verification

Focused initial run: 17 tests, 15 pass, two native Windows installer skips.
Changed-surface follow-up: 13/13 pass. Full suite at `3c68f31`: 600 tests in
115 classes, nine skips, three failures, 465 seconds. The retained gates caught
three omissions: updater module inventory, new-option help, and stale README
recipe strings. Corrections at `9f54e73` received 51 focused tests: 49 pass,
one Windows skip, one error in the new negative control's missing fixture init.
That fixture was corrected at `3aac8ae`; the new missing-recovery-module updater
negative control passes and preserves HEAD/state/journal. All original failed
full-run cases now pass; unchanged full-run evidence is reused. No second full
run is claimed.

Full-run skips: Windows Git Bash launcher; Windows missing symlink privilege;
three Windows suspended Job Object paths; Windows junction parent; two native
PowerShell installer journeys; optional shared-context fixture without its
explicit canonical inputs. Native platform and host-loading obligations remain
on their live RFC/cards. The configured role route does not establish host loading.

Fresh clone at `3c68f31`, with empty home, no installed skill links and restricted
system PATH: documentation gate passes; missing companion fails exit 2; invalid
board fails exit 1; contributor public CLI smoke and all seven rebind cases pass.
The explicit AgentSkills source argument replaces an ignored installed-helper
import. No MASK runtime pip dependency was added. The companion examples (2/2),
four-skill RFC bundle/all 18 packages, and selected imports through both adapters
and two consumers pass with the real MASK CLI. Later corrections affect the
updater inventory, help, recipe expectations and a test fixture; their affected
launcher/update/README/recovery checks pass. An initial new fixture omitted
`--no-update` and attempted program refresh; authentication refused before effects.
Program HEAD, origin/main and files remained unchanged; its home/state were
always disposable. The corrected fixture explicitly skips that refresh.

HTTPS default installer and explicit authenticated gh route pass disposable
macOS shell tests. The public-default test redirects only the exact HTTPS URL
to a local bare fixture. Updated PowerShell source retains native verification
as pending. All 24 changed Markdown files' local links resolved. Documentation:
24 RFCs, 140 cards, zero structural violations; whitespace check passes.

CI uses pinned official actions, read-only contents permission and no persisted
checkout credentials. Private preparation runs the MASK suite and explicitly
requires local companion checks. Public CI requires companion checkout,
documentation and all three integration entrypoints; failures are not skipped.
Once both repositories are public, manually dispatch each repository's
**Source checks** workflow to exercise its public companion-checkout branch.
Visibility changes alone do not trigger these push/pull_request/workflow_dispatch
workflows. Local companion passes and private CI are separate evidence.
SECURITY describes Git refresh effects and the owner action to enable/confirm
private reporting at the visibility switch. No root LICENSE has been adopted.

## Privacy and continuation

Current mutable narrative/fixtures replace avoidable personal roots and project/
host labels. Six historical checkpoint/amendment records change only 24 root/
common-directory strings in `repository_state` (including nested prior_checkpoint).
Mandates, decisions, bindings, fingerprints and observed commit IDs are retained.
They are labeled sanitized historical runtime records, not original replayable
identity checkpoints. Unchanged recorded fingerprints refer to their original
observations; no altered packet integrity or replay is claimed.

Immutable packets and Git history were preserved. Specifically,
`docs/rfcs/assets/upgrade-auto-commit/DRAFT_CHECKS.md` lines 9 and 10 still expose
personal paths; earlier history retains metadata. Public source preview is
conditional on the existing owner license choice/adoption, carried by MASK-0140.
Signed releases, fleet, vault/MCP work and pending native/attended migrations have
not been completed by this bounded preparation. Detailed commands, original
failures, exact runtime paths, privacy classification and final scan/push receipts
remain in private runtime evidence; the coordinator receives the durable handoff.
