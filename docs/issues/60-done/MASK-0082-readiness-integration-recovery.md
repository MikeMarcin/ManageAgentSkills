---
schema: "implement-rfc.card.v1"
id: "MASK-0082"
title: "Resolve readiness integration and recovery regressions"
status: "Done"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0025", "MASK-0026", "MASK-0081"]
acceptance: [{"criterion":"RFC-MASK-0006 integration and recovery","outcome":"pass","revision":"c0d37e78d72802c90ae73f39a7d9e342612494f1","evidence":{"kind":"command","detail":"Full integration at runtime revision 3a8182f ran 123 tests: 119 passes, three skips, one hook recovery failure. The reused path variable is fixed. The 33 affected Git/ensure/lifecycle/host tests all pass (47.140s), covering new-interpreter journal refusal, no unused-package dependency in inactive cleanup, and registered nested consumers without a filesystem crawl. Earlier 29 affected recovery/integration tests passed; unchanged full-suite results are reused."}}]
---

# MASK-0082: Resolve readiness integration and recovery regressions

Own mask_fs.py, mask_integration.py, direct lifecycle/integration regression tests and affected acceptance documentation. The integration pass reported a failure whose completed diagnostic must be consumed before choosing its fix. Review also found that inactive cleanup recovery revalidates cached packages even when their owned links are being removed.

Acceptance: resolve the concrete integration failure and add direct recovery coverage proving inactive cleanup can finish without unused packages. Preserve changed-input refusals, old journal readers and typed integration entry authority. Inspect malformed integration-journal handling; no arbitrary interpreter or write target may be introduced by a new installation journal. Run only affected checks after the integration suite's result is known; unchanged passing evidence remains relevant.

Required discovered card for RFC-MASK-0006. No Windows or host-loading acceptance is fabricated.

Related execution-path check: global Git events must include already registered nested consumers in the same worktree, without discovering unregistered directories or entering nested repositories. Add mask_ensure.py and a direct Git-event fixture to this card’s owned paths and acceptance.
