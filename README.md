# MASK — Manage Agent SKills

MASK is a Python 3.11+ CLI for a private local skill checkout and explicit project declarations. Run it directly with a known interpreter:

```sh
python3 /absolute/path/to/ManageAgentSkills/mask.py capabilities --json
```

Capabilities describes implemented commands, arguments and effects. All machine responses use the versioned JSON envelope, including parser errors. See [the CLI contract](docs/architecture/cli-contract.md) for command details and exit codes. All listed v0.1.0 commands are implemented.

Initialize a machine with `init --source /absolute/path/to/AgentSkills`, inspect `skill list`, create a project declaration with `project init --project PATH`, and edit it with `project require ID` or `project unrequire ID`. `project set --skill ID` replaces the whole membership; `--clear` explicitly empties it. Use `--json` and `--dry-run` for previews. Registration is separate: `project register PATH`. Membership commands preserve unrelated requirements and repeat without rewriting files.

`.mask.json` contains portable skill IDs and optional targets. Complete workflow context is project-local under `.mask/skill-config/implement-rfc/`. `MASK_HOME` (or `--home`) selects machine state, defaulting to `~/.mask`. Source configuration and runtime program location are distinct. Runtime dependencies are Python and Git only; no package download, credential store, daemon, push or automatic synchronization is involved.

Skills are inspected passively using the `mask-package-v1` frontmatter subset: single-line plain or quoted name/description scalars. MASK never executes a skill installer or hook. Source links/special entries, unsafe IDs, duplicate JSON keys and unsupported schema versions refuse.

Register then preview `plan --project PATH`; apply with `apply --project PATH --expect-plan-hash HASH`. Manifest edits can include `--apply --dry-run` to preview the entire prospective deployment. A collision preserves both the manifest and links. Never bypass a collision by deleting user content. `link adopt` records only an exact existing declared skill link with an explicit expected source.

`doctor --all --check` reports drift without repairing it. For interrupted writes, use `recover --inspect`, then explicit `--complete` or `--rollback`. Recovery preserves unexpected content and never resets Git. `project unregister PATH` removes only unchanged owned symlinks and preserves the declaration; `--keep-links` explicitly abandons ownership, including for an unavailable project. Empty created directories are retained and reported after rollback.

Native symlink/recovery checks passed on macOS 26.6.2 and Windows 11 build 26200 with Python 3.14. Windows requires directory symlink privileges; MASK does not elevate or fall back to junctions/copies. The native Windows privilege-error mapping is tested by injecting winerror 1314. Launcher, process-tree timeout, frozen-update, recovery and end-to-end checks also passed on both native platforms. Python 3.11+ is the supported API baseline; these native runs used Python 3.14. Linux remains best-effort and was not part of native acceptance.

Keep repository visibility and inherited-source licensing unchanged. Follow CONTRIBUTING.md, docs/rfcs/README.md and docs/issues/README.md for implementation. Generated machine state is not project source; no ordinary operation requires editing it by hand.

Install a launcher using the selected interpreter:

```sh
python3 /absolute/path/to/ManageAgentSkills/mask.py self install --bin-dir /absolute/path/to/bin --json
```

On Windows use a known supported interpreter (for example `py -3.14`) for this bootstrap command. MASK writes `mask.cmd` there; POSIX writes `mask`. The launcher records the actual interpreter and checkout paths, quotes spaces, forwards arguments and preserves the exit code. It refuses an unrelated or edited existing launcher. MASK does not change PATH: use the returned absolute launcher immediately, or manually add its directory to PATH if desired. `self status --json` reports discovery and ownership. Installation itself does not configure a skill source.

To review a fresh source update, run `source fetch --json`, then `update --dry-run --json`, then `update --expect-plan-hash HASH --json` with the returned hash. Dry-run never fetches and is labeled last-fetched. Update validates a frozen candidate against every registered live declaration, then fast-forwards and reconciles all consumers. Dirty/ahead/diverged/detached or unavailable/colliding projects block; no reset, stash, clean, push or automatic merge is attempted. A shared checkout changes content visible through all links immediately; update between active tasks because hosts may cache instructions.

`self update --json` independently fast-forwards the running ManageAgentSkills checkout, verifies the v1 protocol and unchanged schema contracts, and reports `next_invocation_required`. It does not re-execute, update AgentSkills, reinstall or apply links. Ordinary local skill management works while the program checkout is dirty. Existing noninteractive Git authentication is used; user Git credential helpers and checkout filters remain trusted subprocesses, so MASK is not a sandbox. Timeouts terminate the created process tree; uncertain checkout effects retain recovery intent.

After a partial update, inspect `recover --inspect --json`. Complete only matching recorded intent; rollback never resets an advanced Git checkout. Changed manifests, links or launchers are preserved and block recovery. `project unregister PATH --json` leaves the project's manifest/context and both repositories intact. For an unavailable project, `--keep-links` explicitly abandons its ownership. To remove MASK completely, first unregister the selected consumers, then explicitly remove only the verified owned launcher/program checkout as an ordinary user action, preserving source history and bootstrap backups. There is no purge command. Source relocation is an explicit unregister/setup/register operation; preserve the existing machine directory when setting up another with `--home PATH`.

The named dogfood installation manages only ManageAgentSkills and AgentSkills. Each declares both shared skills and keeps its own workflow context. Verified bootstrap backups remain in each `.mask/bootstrap-retired/implement-rfc-2026-09-05`, outside discovery paths. No source payload is copied into a persistent project fork. See [v0.1.0 readiness](docs/releases/v0.1.0.md) for actual platform evidence, handoffs and limitations.
