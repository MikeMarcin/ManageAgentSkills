# MASK — Manage Agent SKills

MASK is a Python 3.11+ CLI for a private local skill checkout and explicit project declarations. Run it directly with a known interpreter:

```sh
python3 /absolute/path/to/ManageAgentSkills/mask.py capabilities --json
```

Capabilities describes implemented commands, arguments and effects. All machine responses use the versioned JSON envelope, including parser errors. See [the CLI contract](docs/architecture/cli-contract.md) for command details and exit codes; commands marked unimplemented refuse explicitly.

Initialize a machine with `init --source /absolute/path/to/AgentSkills`, inspect `skill list`, create a project declaration with `project init --project PATH`, and edit it with `project require ID` or `project unrequire ID`. `project set --skill ID` replaces the whole membership; `--clear` explicitly empties it. Use `--json` and `--dry-run` for previews. Registration is separate: `project register PATH`. Membership commands preserve unrelated requirements and repeat without rewriting files.

`.mask.json` contains portable skill IDs and optional targets. Complete workflow context is project-local under `.mask/skill-config/implement-rfc/`. `MASK_HOME` (or `--home`) selects machine state, defaulting to `~/.mask`. Source configuration and runtime program location are distinct. Runtime dependencies are Python and Git only; no package download, credential store, daemon, push or automatic synchronization is involved.

Skills are inspected passively using the `mask-package-v1` frontmatter subset: single-line plain or quoted name/description scalars. MASK never executes a skill installer or hook. Source links/special entries, unsafe IDs, duplicate JSON keys and unsupported schema versions refuse.

Register then preview `plan --project PATH`; apply with `apply --project PATH --expect-plan-hash HASH`. Manifest edits can include `--apply --dry-run` to preview the entire prospective deployment. A collision preserves both the manifest and links. Never bypass a collision by deleting user content. `link adopt` records only an exact existing declared skill link with an explicit expected source.

`doctor --all --check` reports drift without repairing it. For interrupted writes, use `recover --inspect`, then explicit `--complete` or `--rollback`. Recovery preserves unexpected content and never resets Git. `project unregister PATH` removes only unchanged owned symlinks and preserves the declaration; `--keep-links` explicitly abandons ownership, including for an unavailable project. Empty created directories are retained and reported after rollback.

Native symlink/recovery checks passed on macOS 26.6.2 and Windows 11 build 26200 with Python 3.14. Windows requires directory symlink privileges; MASK does not elevate or fall back to junctions/copies. The native Windows privilege-error mapping is tested by injecting winerror 1314. Source/program updates and launcher checks follow subsequent live RFC cards.

Keep repository visibility and inherited-source licensing unchanged. Follow CONTRIBUTING.md, docs/rfcs/README.md and docs/issues/README.md for implementation. Generated machine state is not project source; no ordinary operation requires editing it by hand.
