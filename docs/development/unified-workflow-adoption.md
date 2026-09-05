# Shared workflow adoption — 2026-09-05

Approved design and full Q&A: [plan](unified-rfc-workflow-plan-and-interview.md).
Implementation is tracked in AgentSkills RFC-ASK-0003 (ASK-0008–ASK-0014).

This checkout now uses canonical v2 external context and versioned multi-RFC
cards (18 cards, 4 RFCs). Markdown bodies and actual RFC/card status are
unchanged. Shared implement-rfc, attended-review and wizard are deployed through
MASK for Codex and Claude; manage-agent-skills remains required. Guarded previews
and doctor checks passed; generated adapters were regenerated explicitly.

The public documentation gate and board queue passed. Native Windows and macOS
public skill tests ran from disposable fixtures in the AgentSkills integration;
no MASK runtime/application build was required for metadata adoption. MASK still
installs only data/links and never executes these session tools during install.
Host discovery/loading by an already-running agent was not asserted.

One-off converters live outside durable skills and are removed after all
consumer cutovers. No remote push, new credentials, service or daemon was added.
