# Original intake

Source: the owner's Codex conversation in the ManageAgentSkills checkout,
2026-10-03. The owner explicitly invoked author-rfc.

Original request, preserved verbatim:

> It's getting annoying to deal with uncommitted mask lock files every time i upgrade skills. I want an option on mask upgrade to auto commit those changes

Answered questions, preserved verbatim:

1. Question: Should `mask upgrade --commit` commit `.mask.lock.json` plus `.mask.json` when the upgrade changes bundle selections?
   Answer: Commit both when changed (Recommended)
2. Question: If a MASK declaration or lock already has uncommitted changes before the upgrade, should `--commit` include them?
   Answer: Include existing MASK changes (Recommended)

These answers settle only their respective decisions. No answer confirming the
complete draft, aggregate behavior or Git failure policy has been received.

Editorial feedback, preserved verbatim:

> Seems maybe a bit verbose for such a simple feature request

The working draft was shortened without changing behavior or treating this feedback
as confirmation of the remaining proposals.
