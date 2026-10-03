# Canonical AgentSkills bundle handoff

This bounded 2026-10-02 handoff implements only the named RFC bundle portion of
MASK-0064. Upstream owns the real [ASK-0095 card](../../../AgentSkills/docs/issues/60-done/ASK-0095-canonical-rfc-bundle.md)
under RFC-ASK-0015; its mutable tracker is not copied here. Canonical source candidate
`fb67261a5fd8a69231e963226189fd98458e4d82` adds source index schema v1 with all 16
existing packages and flat `agentskills/rfc`: author-rfc, grill-rfc, grill-me,
implement-rfc. Individual installation remains supported.

The upstream README names grill-rfc's author-rfc/grill-me companions and
implement-rfc's portable kit, then gives the public fetch/show/preview/hash-apply/status
sequence. The fixture check is `python3 -B scripts/verify_rfc_bundle.py --mask-program
/absolute/path/to/ManageAgentSkills` from AgentSkills. It uses a disposable local bare
remote, consumer and MASK_HOME, validates every package, installs all four skills for
both discovery adapters, publishes reviewed implement-rfc setup and checks readiness.
Upstream ASK-0095 completed at `b9e413673b7dc7b618487def3831049451010632`.
Final exact-candidate evidence is recorded in
[named-bundle evidence](named-bundles-evidence.json).

No publication, real consumer deployment, credentials, persistent approvals or host
loading observation occurred. The remainder of MASK-0064's management/provenance/fleet
guidance and prerequisite closeouts remains open; this handoff does not close RFC-0017.

## Command vocabulary follow-up

Owner-authorized `named-bundles-v3` changes the public vocabulary to bundle
install/uninstall/upgrade. Real upstream ASK-0096 updates canonical instructions
and verifies safe removal/reinstall while retaining a manually selected companion.
MASK-0128 implements the runtime. Prior revisions above remain historical evidence.
The owner selected combined definition/unheld versions and installed bundles in
ordinary scoped and aggregate upgrade; final exact verification is recorded below.
No broader handoff is accepted.

Independent amended candidate `de0d3736f4767ac1af49f30f336f6a9c2bcd0314` verified
against MASK `d31bf5cbbf85283e275f9668ae8ff8c702b9ddbc`: all four skills ready
with reviewed setup; all 16 packages remain discoverable; offline uninstall
retains manually installed grill-me; repeat no-op and healthy reinstall pass.
[Actual canonical receipt](../../../AgentSkills/docs/development/rfc-bundle-install-uninstall-evidence.json)
binds both prior candidates; this independent checkpoint is historical. No broader
MASK-0064 acceptance or actual host loading is implied.


## Completed combined-upgrade handoff

ASK-0096 completed at `ff9d05a15c767422d00d4f815297bbb3c5a7d5aa`.
Canonical source/verifier `39a6de558252eb0bf8c3cf9ae0d48f3fb10fa0ee` with MASK
`b879f8136489a98cfa26e0aae1da7e7e268c589b` passed
[22 actual public commands](../../../AgentSkills/docs/development/rfc-bundle-upgrade-evidence.json):
all four skills ready with reviewed setup; all 16 packages remain discoverable and
validate; offline removal preserves manually selected grill-me, repeat no-op and
healthy reinstall. Named combined upgrade preview and guarded `upgrade --all`
application adopt a separate derived local fixture definition/package revision;
healthy status and repeat no-op pass. Current public commands are bundle
list/show/install/uninstall/upgrade; default scoped and aggregate upgrade include
installed receipts. Individual skill installation remains available.

RFC-ASK-0015 returns to Auto-Verified at its source-only boundary; MASK-0128 owns
runtime acceptance. The verifier ended and its temporary tree/remotes/machine roots
were cleaned. No source push/publication, real consumer deployment, credential or
permission change, running-host loading or native Windows acceptance is claimed.
Broader MASK-0064 stays Backlog.
