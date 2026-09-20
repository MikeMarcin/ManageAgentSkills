# Contributing to ManageAgentSkills

Use the live RFC and local issue-board contracts. The implement-rfc skill automates this process, but human contributors can satisfy the same requirements without a particular agent. Read root/nested instructions, claim a bounded card, implement only owned paths, run focused acceptance checks, keep docs truthful, and commit explicit paths.

Do not treat a detailed RFC packet as completed work. Record actual baseline/integration commits and leave unavailable native-platform cards open. No mandatory broad test matrix or model/runtime subscription is implied. Tests use disposable local fixtures; live private source/auth changes require explicit scope.

Use existing Git authentication and avoid adding credentials to skills, config, output or logs. Public projects must keep their contributor contract readable without access to private skill content.

When changing shared skill content, edit the canonical AgentSkills source through ordinary Git, not a per-project copy. MASK links consumers to locked store copies of a tap, so an edit reaches them only after it is pushed and `mask upgrade` runs (or through an explicit `skill dev-link`). MASK has no automatic commit/push or writeback synchronization. During the one-time bootstrap phase, follow the recorded temporary-copy instructions and retire those copies at cutover.
