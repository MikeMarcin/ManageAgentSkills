---
schema: "implement-rfc.card.v1"
id: "MASK-0082"
title: "Resolve readiness integration and recovery regressions"
status: "In Progress"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0025", "MASK-0026", "MASK-0081"]
---

# MASK-0082: Resolve readiness integration and recovery regressions

Own mask_fs.py, mask_integration.py, direct lifecycle/integration regression tests and affected acceptance documentation. The integration pass reported a failure whose completed diagnostic must be consumed before choosing its fix. Review also found that inactive cleanup recovery revalidates cached packages even when their owned links are being removed.

Acceptance: resolve the concrete integration failure and add direct recovery coverage proving inactive cleanup can finish without unused packages. Preserve changed-input refusals, old journal readers and typed integration entry authority. Inspect malformed integration-journal handling; no arbitrary interpreter or write target may be introduced by a new installation journal. Run only affected checks after the integration suite's result is known; unchanged passing evidence remains relevant.

Required discovered card for RFC-MASK-0006. No Windows or host-loading acceptance is fabricated.
