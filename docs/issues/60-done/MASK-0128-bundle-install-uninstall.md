---
schema: "implement-rfc.card.v1"
id: "MASK-0128"
title: "Amend bundles to install, uninstall and combined upgrade"
status: "Done"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0042"]
external_depends_on: ["AgentSkills:ASK-0096"]
metadata: {"milestone_plan":{"id":"named-bundles","path":"docs/rfcs/plans/named-bundles/milestone-plan.json"}}
acceptance: [{"criterion":"install-uninstall-ownership-and-recovery","outcome":"pass","revision":"b879f8136489a98cfa26e0aae1da7e7e268c589b","evidence":{"kind":"artifact","path":"docs/development/named-bundles-combined-upgrade-acceptance.json","detail":"Public additive install, bounded replacement, offline local receipt removal, manual/overlap/hold/edit preservation, no-op/reinstall, stale plans and frozen completion/rollback pass. Earlier exact d31bf5c receipt remains historical."}},{"criterion":"combined-named-default-and-all-upgrade","outcome":"pass","revision":"b879f8136489a98cfa26e0aae1da7e7e268c589b","evidence":{"kind":"artifact","path":"docs/development/named-bundles-combined-upgrade-acceptance.json","detail":"Definition changes plus newer unheld members use the shared resolver and guarded lifecycle. Default scoped and --all include installed receipts and ordinary skills; holds/exact selectors/local edits/shared constraints/stale approvals/partial scopes/setup and frozen recovery pass."}},{"criterion":"canonical-source-handoff","outcome":"pass","revision":"b879f8136489a98cfa26e0aae1da7e7e268c589b","evidence":{"kind":"artifact","path":"docs/development/named-bundles-combined-upgrade-acceptance.json","detail":"Actual ASK-0096 accepted ff9d05a, canonical source 39a6de5 with MASK b879f81 passed 22 public commands: all four ready, 16 packages discovered/validated, offline manual-safe uninstall/reinstall, combined named preview and aggregate derived-fixture upgrade."}},{"criterion":"docs-capabilities-and-upkeep","outcome":"pass","revision":"b879f8136489a98cfa26e0aae1da7e7e268c589b","evidence":{"kind":"artifact","path":"docs/development/named-bundles-combined-upgrade-acceptance.json","detail":"Current help/capabilities/docs advertise only list/show/install/uninstall/combined upgrade; canonical companions/individual install retained. Documentation gates, explicit commits and quiescent continuation recorded in closeout."}}]
---

# Amend bundles to install, uninstall and combined upgrade

Owner amendments, 2026-10-02, mandate `named-bundles-v3`: replace pre-release
apply/refresh with install/upgrade, add ownership-safe uninstall, combine bundle
definition changes and newer unheld member versions, and include installed
bundles in `mask upgrade --all`. Owner explicitly answered "yes go with
recommendation". Same adopted named-bundles plan and preserved coordinator-
implementer strategy; historical MASK-0042 acceptance stays intact.

Install is additive. Explicit `install --replace` replaces only the named local
membership contribution and preserves existing exact package rows. Uninstall
uses a frozen local receipt without current source acquisition; it removes only
unchanged exclusive members, preserves manual/overlapping selections and promotes
held/edited last-origin survivors to manual membership. Reinstall creates a new
receipt and preserves those survivors. Ordinary standalone `uninstall ID` remains
an explicit removal of that selection and its frozen expanded membership.

Named upgrade recomposes the selected definition and resolves only its eligible
incoming member coordinates through the ordinary resolver. Default scoped upgrade
and `upgrade --all` recompose installed receipts together, combine ordinary selected
skills, and use one guarded review/planner/setup/journal. Selected-ID upgrade keeps
bundle definitions frozen. Shared members advance only with compatible selectors;
conflicting versions/conditions/targets report origins before consumer changes.
Manual target overrides, exact selectors, pins and local edits remain protected.

[Final acceptance](../../development/named-bundles-combined-upgrade-acceptance.json)
binds runtime `b879f8136489a98cfa26e0aae1da7e7e268c589b` and actual upstream
ASK-0096 source `39a6de558252eb0bf8c3cf9ae0d48f3fb10fa0ee`, accepted at
`ff9d05a15c767422d00d4f815297bbb3c5a7d5aa`. All 43 public bundle/renderer tests
succeeded; an extra invalid regression selector produced one loader error,
retained in its mechanical receipt and corrected by the separate passing scoped
regression. Correction rerun plus all 17 ordinary update tests passed (19 total).
Canonical 22 public commands verify all four RFC skills ready with reviewed setup,
all 16 packages preserved, manual-safe offline uninstall/reinstall, and combined
aggregate upgrade of a separate derived fixture update. Historical failures and
corrections remain explicit; no unresolved product failure remains.

No required human review. Product/test/setup commands ended and fixtures were
cleaned; no server, worktree or extra writer. Preserve open profile/export/fleet/
native-host obligations and RFC-MASK-0010 status. No push, real consumer migration,
credentials or permission changes.
