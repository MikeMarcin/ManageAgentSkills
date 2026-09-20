# Accepted MASK 0.3 command surface

Owner-approved on 2026-09-20, including the pin/unpin amendment during implementation.
This document replaces the earlier all-registered default and public ensure proposal.

| Bucket | Commands | Default target |
|---|---|---|
| Shared resources | tap, untap, update, cleanup | MASK program/catalog/storage |
| Catalog browsing | search, info | Shared approved tap catalogs |
| Enrollment | register, unregister | Current checkout; --user is explicit |
| Skill selection | install, uninstall, list, pin, unpin | Current checkout; --user is explicit |
| Maintenance | upgrade, repair, status | Current checkout; --user or --all is explicit |

An installation is one checkout/worktree or the personal skill selection. Bare
maintenance never also selects personal skills. Outside a checkout, select a target.
Upgrade --all is the single personal-maintenance command for every registered
checkout plus personal skills. Pin/unpin --all instead replaces the SKILL operand:
it selects all skills in the chosen checkout, or all personal skills with --user.

Register [PATH] enrolls and prepares a fresh checkout using its existing locked
versions. Install/uninstall reconcile the selection in the same task. Repair
restores declared pins. Upgrade moves eligible selections forward and restores
readiness even for unchanged or explicitly held versions. Pin sets a declarative
version hold on the existing lock; unpin releases it without upgrading immediately.

Each task resolves, inspects, reviews significant actions, applies and verifies.
Setup and exact native-role replacements share one review before consumer writes.
Decline or missing consent leaves declaration, lock, registry and deployment intact.
Acquired caches may remain and are disclosed. --approve-plan HASH approves exactly
the previewed task. Ordinary owned effects require no extra question. Preview and
reviewed application do not fetch. There is no --yes, --repair or --yolo bypass.

Update refreshes MASK itself and shared taps. Install/upgrade perform that refresh
when the last successful refresh is older than 24 hours, unless --no-update or
--offline. Operation-specific acquisition is still permitted with --no-update;
--offline forbids it too. A program update re-executes before consumer planning.

Cleanup is explicit and reviewable. It removes verified unused artifacts, unused
owned source caches, disposable backups and recognized retired generated files.
It preserves referenced content, current lock files, pending recovery and unknown
content. A lifecycle lock protects preparation as well as publication. Partial
or unknown staging without surviving ownership evidence is retained and reported.

CLI and result JSON move to 0.3/protocol v2. Old public ensure, plan, apply, doctor,
remove, inventory and split initialization/registration commands retire. Private
operation IDs and readers remain to recover existing journals and run integrations.
Advanced source operations move under tap; development linking moves under skill.
Adapters use integration run; the upstream preflight negotiates status versus the
older ensure from advertised capabilities. Publication/deployment is a separate
owner-controlled action; source edits do not change installed AgentSkills payloads.
