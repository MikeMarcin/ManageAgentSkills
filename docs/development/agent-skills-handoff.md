# Canonical AgentSkills bundle handoff

This bounded 2026-10-02 handoff implements only the named RFC bundle portion of
MASK-0064. Upstream owns the real [ASK-0095 card](../../../AgentSkills/docs/issues/30-in-progress/ASK-0095-canonical-rfc-bundle.md)
under RFC-ASK-0015; its mutable tracker is not copied here. Canonical source candidate
`fb67261b` adds source index schema v1 with all 16
existing packages and flat `agentskills/rfc`: author-rfc, grill-rfc, grill-me,
implement-rfc. Individual installation remains supported.

The upstream README names grill-rfc's author-rfc/grill-me companions and
implement-rfc's portable kit, then gives the public fetch/show/preview/hash-apply/status
sequence. The fixture check is `python3 -B scripts/verify_rfc_bundle.py --mask-program
/absolute/path/to/ManageAgentSkills` from AgentSkills. It uses a disposable local bare
remote, consumer and MASK_HOME, validates every package, installs all four skills for
both discovery adapters, publishes reviewed implement-rfc setup and checks readiness.
Final exact-candidate evidence and upstream completion revision are recorded in
[named-bundle evidence](named-bundles-evidence.json).

No publication, real consumer deployment, credentials, persistent approvals or host
loading observation occurred. The remainder of MASK-0064's management/provenance/fleet
guidance and prerequisite closeouts remains open; this handoff does not close RFC-0017.
