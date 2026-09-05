---
id: RFC-MASK-0001
title: Agent-friendly CLI and declarative project state
status: Proposed
owner: MikeMarcin
created: 2026-09-05
---

# RFC-MASK-0001: Agent-friendly CLI and declarative project state


## Summary

Build the command and configuration contract for MASK without a third-party Python runtime dependency. An agent can discover the CLI, inspect source skills, edit a project declaration, register projects, and preview effects without editing internal state. The CLI is the management API; JSON files remain transparent recovery artifacts.

## Scope

Own `mask.py`, `schemas/**`, focused CLI/config/registry tests, root instructions and relevant documentation. This RFC defines reconciliation interfaces but does not claim symlink mutation or remote update acceptance; those are RFC-MASK-0002/0003. Use the shared implementation skill from RFC-ASK-0001. The cross-repository handoff records its actual commit before this RFC's implementation begins.

## Files and schema policy

Human and tool-authored project declaration:

```json
{
  "schema_version": 1,
  "skills": ["implement-rfc"],
  "targets": ["claude", "codex"]
}
```

Location: `<project>/.mask.json`. `skills` is a set serialized as a sorted unique array. `targets` is optional; absence means the machine's configured default targets. An explicit target list is nonempty and contains only `claude`/`codex`. No repository URLs, credentials, absolute paths, shell commands, install hooks, project version constraints or dependency resolver are allowed here.

`MASK_HOME` defaults to `~/.mask`. Its `config.json` contains schema version, one absolute `source.root`, expected Git `source.remote` and `source.branch`, `default_targets`, and `git_timeout_seconds`. Default remote/branch are `origin`/`main`; overrides are explicit. The running program root is derived from `mask.py`, not mistaken for the skill source.

`state.json` contains a monotonically increasing generation, canonical project records, last observed manifest data/digest, and exact managed-link records. It contains no credentials or remote device state. RFC-MASK-0002 specifies ownership and recovery. Missing initial machine state is a valid empty registry; malformed/future-version state is an error, never an empty registry.

Strict JSON reading rejects duplicate object keys, booleans where integers are expected, non-finite numbers, unknown schema versions, unknown fields and wrong types. Writers use UTF-8, LF, two-space indentation and trailing newline. Canonical hashing uses compact sorted-key JSON with the same semantic set normalization, not display formatting. A no-op must not churn timestamps, generations, file bytes or Git diffs.

## Skill package boundary

The library is flat: `skills/<id>/SKILL.md` with arbitrary regular supporting files/directories. IDs are lower-case ASCII hyphenated tokens, 1–64 characters; reject traversal, separators, absolute/drive paths, leading dashes, Windows reserved device names, trailing dots/spaces, and Claude's reserved `synced` name. Case-fold collisions refuse even on case-sensitive hosts so the same source works on Windows/macOS.

v1 supports a documented **MASK frontmatter subset**, not all YAML: `name` and `description` must be top-level plain/quoted single-line scalars; optional other frontmatter is preserved as opaque text. For this personal library, migrate an unsupported description representation deliberately or return `skill.metadata_unsupported`; do not guess by stripping arbitrary YAML. `name` must equal the skill ID; description must be nonempty. No evaluation of YAML tags/objects or dynamic commands. `skill validate` labels its scope `mask-package-v1`, not full Agent Skills conformance. `agents/openai.yaml` and other supporting metadata are not executed or parsed by MASK.

A source skill root, SKILL.md or supporting entry may not be a symlink, junction, submodule or other special filesystem object in v1. Reject rather than following escaping paths. A normal text/script/asset file is allowed, but MASK never executes it.

## Public commands

The normative inventory is `docs/architecture/cli-contract.md`. Principal commands:

```text
mask init --source PATH [--target claude --target codex]
mask config show
mask config set [--target TARGET ...] [--git-timeout SECONDS]
mask capabilities
mask skill list
mask skill show ID [--content]
mask skill validate [ID | --all]
mask project init [--project PATH]
mask project show [--project PATH]
mask project set --skill ID ... [--project PATH] [--apply]
mask project set --clear [--project PATH] [--apply]
mask project require ID ... [--project PATH] [--apply]
mask project unrequire ID ... [--project PATH] [--apply]
mask project set-targets TARGET ... [--project PATH] [--apply]
mask project set-targets --inherit [--project PATH] [--apply]
mask project register [PATH | --project PATH] [--apply]
mask project unregister [PATH | --project PATH] [--keep-links]
mask project list
```

All support `--json`; mutators support `--dry-run`. The later RFCs add plan/apply, explicit link adoption, recovery, doctor, updates and launcher commands. Do not ship stubs reporting success for unfinished effects; unavailable commands return a version/capability error until implemented.

`init` validates an existing local source checkout; it does not clone, authenticate or access GitHub. Repeating the identical setup is a no-op. Different already-configured source values refuse `config.already_initialized`; moving the source is intentionally not a v1 routine operation. Agent recovery is unregister, re-establish setup in a new MASK_HOME, then register/apply; never silently retarget existing links. `config set` can change defaults/timeouts only; it does not apply projects automatically.

## Project selection and edits

An explicit project path selects that root and does not search its parents for another declaration. With no path, find the nearest `.mask.json` upward inside the nearest Git worktree boundary. For `project init`, choose the nearest Git worktree root; outside Git require an explicit root. A directory without Git may be explicitly registered, but `.mask.json` must exist. Never discover siblings or auto-register unrelated projects. `register .` is a supported shorthand; providing both positional path and `--project` is an error.

`project init` creates an empty declaration and never overwrites an existing one. `require` is union; `unrequire` is subtraction and can remove an unknown/deleted skill; `set` is replacement and requires at least one `--skill` or explicit `--clear`. Repeated membership operations are successful no-ops. Validate the prospective declaration before writing; a missing requested skill is not silently dropped.

Without `--apply`, edit only the manifest; registration is separate. With `--apply`, require an already registered project and pass the **prospective manifest** to the same complete preflight used by apply. A collision must leave both manifest and links unchanged. Do not create a declaration first and discover a deployment failure afterward.

Registration is machine-local, records the canonical physical project root and its observed identity, and never inserts absolute paths into project Git. One root cannot be registered twice via aliases/case variants. Worktrees are independent projects. Missing/unavailable registered roots remain visible. `unregister` normally removes owned links through the reconciler and then the registry entry while retaining `.mask.json`; `--keep-links` explicitly abandons ownership records and leaves the filesystem unchanged, including when a project is unavailable. Report abandoned paths rather than suggesting they are cleaned.

## Protocol guarantees

`--json` means exactly one versioned JSON document on stdout, including ordinary errors and argument errors; Git output/progress/tracebacks never contaminate it. Success and error share one envelope. `changed` means actual persistent managed effects; `would_change` is a preview field. Plan/dry-run always have `changed=false`. `ok=false` implies a nonzero exit, including incomplete multi-project work and failed rollback.

Error codes, exit classes, actions, transaction states, input flags and remediation are specified in the architecture contract and schemas. `capabilities` exposes argument descriptors, mutation/network flags and supported schemas, not just a list of names. English messages can improve independently of stable codes. Errors include retryability, relevant paths and redacted external-command details.

No prompts, fuzzy skill selection, default destructive answer, `--force` or success-on-partial. Limit diagnostics to bounded sanitized output. An agent cannot authorize itself to publish a repository or delete an unmanaged directory because a remediation string suggested it.

## Verification and limits

Subprocess tests assert actual argv parsing, stdout JSON, exit codes, stderr separation, no-op bytes and source/manifest boundaries. Unknown args with `--json` still produce JSON; help/version with `--json` produce structured information. Tests cover spaced/Unicode project paths, explicit roots, nested CWD and both option placements. Bootstrap and installation do not require Python packaging services or an unrelated PyPI package named `mask`.


## Acceptance criteria

- **RFC-MASK-0001-AC01** — An agent discovers supported commands, argument shapes, schemas and effects through capabilities without reading internal state or source; every completed command returns the versioned envelope.
- **RFC-MASK-0001-AC02** — JSON output is single-document UTF-8 with no mixed logs on all ordinary success/error/parser/help paths; exit codes and stable error codes agree and no-op writes are byte-stable.
- **RFC-MASK-0001-AC03** — Strict project and machine JSON validation rejects unsafe IDs/paths, duplicates, unknown fields/versions and wrong types; skill inspection is passive and reports its validation scope.
- **RFC-MASK-0001-AC04** — Project discovery, explicit paths, worktree roots, incremental edits, exact-set/clear and registration behave deterministically; unavailable entries remain visible.
- **RFC-MASK-0001-AC05** — Project editing can preview a prospective deployment without writing; --apply refuses until the registered-project reconciler is available and later integrates without a separate mutation implementation.
- **RFC-MASK-0001-AC06** — No local command performs network activity or credential handling, and program/source roots are distinct in config and output.
