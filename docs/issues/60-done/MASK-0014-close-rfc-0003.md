---
id: MASK-0014
title: Verify and close RFC-MASK-0003
status: Done
rfc: RFC-MASK-0003
depends_on: ["MASK-0011", "MASK-0012", "MASK-0013"]
closeout: true
---

# MASK-0014: Verify and close RFC-MASK-0003

## Objective and owned paths

Own update/install contract closeout and handoff to the second AgentSkills skill.

## Bounded work

Record actual integrated CLI/protocol commit and available launcher evidence. Do not claim a platform launcher that has not yet run; final native card remains the release gate.

## Acceptance

All source/program update acceptance and launcher contract tests pass at their stated direct boundary; docs list remaining native release checks.

## Focused verification

Structure gate plus missing/invalidated update and launcher tests.

## Run record

Source/program update and launcher acceptance satisfied. Native Windows 11 build 26200 / Python 3.14: launcher, subprocess-policy, Git-update and recovery modules 20 PASS. macOS corresponding focused checks pass as recorded in MASK-0012/0013. No external credentials or remote-host repositories used; only temporary local bare remotes. Structure gate and bounded baseline diff review pass. Final end-to-end/dogfood support checks remain MASK-0015/0016/0017. Commit: this Done move.

## Durable closeout anchor

RFC_BASE_SHA: e0e1e9533a08a2b8327175d0771c9de4dc7d5412

Planned cards: MASK-0011, MASK-0012, MASK-0013.

Cross-repository handoff commits: CLI v0.1.0 integrated f23237d; this closeout hands off to ASK-0005.

Next slice: AgentSkills ASK-0005 management skill; native end-to-end/cutover remain RFC-MASK-0004.

## Closeout checklist

| Acceptance | Direct check / command | Result | Commit |
|---|---|---|---|
| RFC-MASK-0003-AC01 | Frozen candidate/live declarations; tests.test_git_update | PASS | f23237d |
| RFC-MASK-0003-AC02 | Dirty/ahead/diverged/detached/unavailable/case/symlink refusal fixtures | PASS | f23237d |
| RFC-MASK-0003-AC03 | No-fetch preview and moved-ref guarded refusal | PASS | f23237d |
| RFC-MASK-0003-AC04 | Fake helper timeout and auth redaction; checkout/post-advance journals | PASS | f23237d |
| RFC-MASK-0003-AC05 | Native launcher args/exit/owned collision on macOS and Windows | PASS | f23237d |
| RFC-MASK-0003-AC06 | Program-only ff update and protocol-incompatibility refusal | PASS | f23237d |
