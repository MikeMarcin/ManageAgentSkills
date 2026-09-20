# Readiness, setup and integrations

A task succeeds when declared links, native roles and required consumer inputs are
ready on the filesystem. This does not prove that a running agent has loaded them.
Restart running agents after changing their files.

## Choose the task

```sh
mask register          # fresh clone or worktree: enroll and restore declared pins
mask install SKILL     # add a skill and complete setup
mask upgrade           # newer allowed versions and complete setup in this checkout
mask repair            # restore this checkout without moving pinned versions
mask status --check    # inspect only; nonzero when attention is required
```

Add `--user` for personal skills. Upgrade, repair and status accept `--all` for
every registered checkout plus personal skills. Pin/unpin hold or release selected
versions; upgrade still completes setup for held skills.

A passive `mask-workflow.json` package descriptor may declare required consumer
inputs, static native roles and setup actions that generate roles. Consumer inputs
are not invented. Missing or invalid required inputs block the task before consumer
mutation and name the files that need attention.

## One review before changes

MASK builds the complete task before changing declarations, locks, registration or
deployment. Required setup scripts and replacement of edited regular native role
files appear in one terminal review. Declining applies no consumer changes.

```sh
mask upgrade --dry-run --json
mask upgrade --approve-plan RETURNED_HASH --json
```

Preview never fetches, writes or runs package code. Prepare catalog content with
`mask update` or `mask tap fetch` if needed. An approved-plan application does not
refresh content; changed inputs invalidate the hash. JSON and redirected commands
never prompt. There is no blanket `--yes`, `--repair`, `--yolo` or separate setup grant.

The review identifies the package, content fingerprint, interpreter, script, roots
and generated roles. Replaced regular role files receive durable backups under
`MASK_HOME/backups`. Skill-directory collisions and unsafe paths remain protected.
Explicit `cleanup` can later remove verified disposable backups.

Setup runs in an owned staging directory with a versioned request and bounded
process/output limits. MASK validates requested native role files before journaled
publication. Setup code is not sandboxed; the approval is permission to execute the
named package action. A script failure leaves a nonzero result and reports earlier
committed effects honestly. Recovery never reruns a script.

Descriptors can supply a separate `scopes.user` contract. Personal setup is rooted
in the registered home and need not require project context. Native role destinations
are `.codex/agents/` and `.claude/agents/`. The generated lock lives under
`.mask/generated/SKILL/native-roles.lock.json`. The older skill-config lock is a
fallback while it remains in use; cleanup removes it only when a verified replacement
and complete current workflow make it disposable.

## Optional automatic readiness

Explicit register/install/repair/upgrade need no standing readiness grant. Automatic
Git and host events retain their separate, explicit physical-root authority:

```sh
mask integration approve --project /path/to/project --dry-run --json
mask integration approve --project /path/to/project --approve-plan RETURNED_HASH --json
mask integration enable --project /path/to/project --git
mask integration enable --project /path/to/project --agent codex
mask integration inspect --project /path/to/project
```

Approve only the roots or linked-worktree boundary you intend. Enabling an adapter
does not itself grant readiness or setup authority. Generated hooks invoke
`integration run --event EVENT`; events never prompt and never grant package setup.
They restore approved locked deployment and report unmet workflow requirements.
Run an explicit repair when setup needs review.

```sh
mask launch --agent codex
mask integration disable --project /path/to/project --git
mask integration revoke --project /path/to/project
```

Launch uses the same readiness service before starting the selected host. Host
settings and hooks are ownership checked; unrelated settings are preserved.
`status --check --workflow-profile SKILL=PROFILE` supports observational requirement
profiles for workflow helpers. A selected profile cannot suppress core deployment
or source/tracker failures. The canonical AgentSkills preflight negotiates this
entrypoint from capabilities and retains compatibility with older MASK versions.
