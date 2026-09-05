# MASK — Manage Agent SKills

MASK is a Python 3.11+ CLI for a private local skill checkout and explicit project declarations. Run it directly with a known interpreter:

```sh
python3 /absolute/path/to/ManageAgentSkills/mask.py capabilities --json
```

Capabilities describes implemented commands, arguments and effects. All machine responses use the versioned JSON envelope, including parser errors. See [the CLI contract](docs/architecture/cli-contract.md) for command details and exit codes; commands marked unimplemented refuse explicitly.

Initialize a machine with `init --source /absolute/path/to/AgentSkills`, inspect `skill list`, create a project declaration with `project init --project PATH`, and edit it with `project require ID` or `project unrequire ID`. `project set --skill ID` replaces the whole membership; `--clear` explicitly empties it. Use `--json` and `--dry-run` for previews. Registration is separate: `project register PATH`. Membership commands preserve unrelated requirements and repeat without rewriting files.

`.mask.json` contains portable skill IDs and optional targets. Complete workflow context is project-local under `.mask/skill-config/implement-rfc/`. `MASK_HOME` (or `--home`) selects machine state, defaulting to `~/.mask`. Source configuration and runtime program location are distinct. Runtime dependencies are Python and Git only; no package download, credential store, daemon, push or automatic synchronization is involved.

Skills are inspected passively using the `mask-package-v1` frontmatter subset: single-line plain or quoted name/description scalars. MASK never executes a skill installer or hook. Source links/special entries, unsafe IDs, duplicate JSON keys and unsupported schema versions refuse.

Symlink reconciliation, recovery, source/program updates and launcher installation follow subsequent live RFC cards. `--apply` currently refuses until that engine is integrated. No native platform support is claimed by this initial CLI boundary.

Keep repository visibility and inherited-source licensing unchanged. Follow CONTRIBUTING.md, docs/rfcs/README.md and docs/issues/README.md for implementation. Generated machine state is not project source; no ordinary operation requires editing it by hand.
