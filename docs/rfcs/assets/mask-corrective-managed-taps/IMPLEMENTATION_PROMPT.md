# Implement the MASK tap-only deployment pack

Implement RFC-MASK-0020 from this pack in ManageAgentSkills using the
[authored milestone plan](milestone-plan.json). Preserve unrelated work and
closed RFC history. Read the actual local instructions and scoped consumer rules,
then import with live IDs using IMPORT.md and adopt the plan. Record the real
pre-implementation revision in the closeout; do not invent a baseline.

Owner decisions are settled: the live-checkout deployment mode is retired
entirely; taps with MASK-owned bare caches, the content-addressed store and
per-consumer locks are the only deployment model; AgentSkills is an ordinary tap;
`mask update` fetches every referenced tap before re-resolving; existing v1 and
v2 machines, projects and personal scopes are migrated by `mask doctor --migrate`;
`project/user set|require|unrequire` stay for v2 declarations.

Land config v3 and the tap-first fixtures before deleting legacy code so the
suite is green at every card. Use the existing planner, resolver, store, typed
journal and result object. Do not add a copy-deployment fallback, an eager fetch
on `tap add`, pruning, or a second orchestration layer. Links target the store
only; an authoring checkout is for `source publish` and explicit `source
dev-link`.

Migration never resets, stashes, cleans, deletes or pushes the user's clone.
Dirty, unborn, detached or diverged inputs are typed refusals with remediation.
Acquire the clone HEAD into the tap cache from the local clone over file
transport so migration works offline and pins exactly the deployed bytes. One
journal per migration; rollback restores exact prior bytes and links.

Start the regressions from the actual failure shape: an empty `MASK_HOME` that
must bootstrap from `tap add`, and a schema-true v1 machine whose links point
into a clone. Tests must not hide fetches, registration or migration in fixture
setup. Exercise the public CLI as a subprocess: argv, exit code, JSON stdout,
stderr and filesystem/Git effects.

Run focused checks per card and reuse unchanged evidence. Native Windows 11 and
macOS qualification and the owner's attended machine migration stay open until
actually run. Keep the previous program's schema guard; a journal written by
this program is refused by the previous one. Publish README and help only with
working commands, and replay the README before closeout. No push, publication,
credential change or migration of any real machine other than the attended
dogfood card is implied.
