---
id: "RFC-MASK-0022"
title: "Transport-neutral tap identity and convention-following transport"
status: "Implementing"
owner: "MikeMarcin"
created: "2026-09-16"
---

# RFC-MASK-0022: Transport-neutral tap identity and convention-following transport

**Implementing; not qualified.** Filed at the owner's request on September 16, 2026, after an HTTPS/SSH tap mismatch blocked `mask ensure` on a working machine. The owner directed implementation the same day with this RFC's proposed answers to its open questions; AC08 (the SSH-approved machine) remains open, so the closeout is open. Closeout: [MASK-0113](../issues/10-backlog/MASK-0113-close-transport-neutral-tap-identity.md).

Amends RFC-MASK-0007 (source identity normalization) and RFC-MASK-0021 (machine config v3 tap entries and doctor migration). It changes the current contract sentence "HTTPS and SSH stay distinct" in [cli-contract.md](../architecture/cli-contract.md#taps-payloads-and-caches) for recognized forge hosts only. Historical RFCs and evidence remain unchanged.

## Decision

A tap's **identity** names which repository to trust. Its **transport** says how one machine reaches that repository. Today one committed string records both, so a project file can only suit machines that authenticate the same way. This RFC separates them:

1. **Identity is transport-neutral on forge hosts.** On a recognized forge host, `https://H/P`, `ssh://git@H/P` and `git@H:P`, each with or without `.git`, normalize to one identity. Declarations, locks, the machine catalog, cache keys and state compare that identity. The canonical spelling is `https://H/P.git`, so existing HTTPS declarations and locks are already canonical and need no change.
2. **Transport is machine-local and follows convention.** Unless a machine pins a transport for the tap, MASK chooses it, in this order: the pin; the consumer checkout's `origin` scheme when it is on the same host; the host's `gh` `git_protocol` setting; then a noninteractive probe of the remaining candidate. The chosen transport never enters project files.
3. **Strictness stays where it matters.** On any other host, HTTPS and SSH remain distinct identities. A machine may opt a host into forge equivalence in its own configuration. Project files can never make that opt-in.

Transport never changes content trust. Commits, object format and payload digests are verified exactly as today, whichever transport fetched them.

## Evidence and failure mechanism

- `mask_sources.repository` is documented as "Normalize transport spelling without equating HTTPS and SSH authority". `git@github.com:O/R.git` becomes `ssh://git@github.com/~/O/R.git`, and `tests/test_sources.py` asserts it differs from both `ssh://git@github.com/O/R.git` and the HTTPS form. One GitHub repository therefore has three identities.
- `mask_resolve.approved` compares `entry['repository'] != expected['repository']` as plain strings and fails `source.identity_mismatch` ("Selection repository or package layout does not match the machine approval."). The comparison is repeated in `mask_resolve` lock checks, `mask_pinned` link resolution, `mask_provenance` authoring-origin checks, and `mask_sources` catalog lookup and cache markers. `binding` derives the cache path from the identity digest.
- **Between machines.** ExampleReview `0efe3bf1` committed the tap as `https://github.com/MikeMarcin/AgentSkills.git`. A machine approved over SSH failed `mask ensure`, so `eeb16d13` relocked it as `ssh://git@github.com/~/MikeMarcin/AgentSkills.git`. That in turn failed on ExampleOwnerHost, which was approved over HTTPS. `--yes` cannot override this, and no public command rebinds a tap: `tap add` refuses `source.alias_conflict`, and `tap remove` refuses `source.referenced`.
- **On one machine.** ManageAgentSkills' own `.mask.json` pins the HTTPS spelling while ExampleReview pins the SSH spelling. No single machine approval can make both projects ready.
- **The canonical SSH spelling is not a usable GitHub URL.** `git ls-remote ssh://git@github.com/~/MikeMarcin/AgentSkills.git` fails with "is not a valid repository name". Only the scp form `git@github.com:MikeMarcin/AgentSkills.git` or the absolute `ssh://git@github.com/MikeMarcin/AgentSkills.git` works, and those two normalize to different identities today.
- **The only workaround broke a repository rule.** Recovering ExampleOwnerHost on 2026-09-16 required editing `~/.mask/config.json` (identity, transport, cache path) and `~/.mask/state.json` (the project's `last_manifest`, `last_lock`, every `links.*.resolution.repository`, and both selection digests). AGENTS.md forbids editing MASK internal state as a workaround, so the supported product has no path out.

## Contract

**Forge hosts.** The built-in forge set is `github.com`, `gitlab.com`, `bitbucket.org` and `codeberg.org`. Machine config v3 gains an optional `forge_hosts` array of lowercase hostnames that extends the set on that machine only. On a forge host, an HTTPS URL without user info, an `ssh://git@` URL with an absolute path, or an scp `git@H:P` path normalizes to `https://H/P.git`. A non-default port, a user other than `git`, an explicit `/~/` path or any other shape stays strict and keeps its current identity. Normalization still preserves path case and still refuses credentials, queries, fragments, unsafe paths and unsupported schemes.

**Reading existing files.** Every identity comparison goes through the normalizer. A v2 declaration or lock written before this RFC with any forge spelling is read as its canonical identity. Its recorded `selection_digest` is verified against the spelling that is actually recorded. `ensure`, `list`, `doctor` and fetch never rewrite a committed declaration or lock only to change its spelling. `install`, `remove`, `update` and `lock` write the canonical spelling when they otherwise write the file. Payload and metadata digests and commits do not change.

**Tap entries.** A tap entry keeps `repository` (the canonical identity) and gains a `transport_policy` of `derived` (the default) or `pinned`. When the policy is `pinned`, `transport` is authoritative. When it is `derived`, `transport` records the last transport that succeeded, as a hint. `tap add NAME URL` records the URL's scheme as that hint without pinning it, and `--pin-transport` pins it. The new `tap transport NAME URL [--dry-run]` pins a transport, and `tap transport NAME --derive` returns the tap to derived selection. Both refuse a URL whose identity differs (`source.identity_mismatch`) and change nothing but the catalog.

**Transport selection.** Pinned taps use their transport and nothing else. For a derived tap, a fetch builds an ordered candidate list:
1. The consumer checkout's `origin` scheme, when that origin is on the same host. This applies only when the operation selects exactly one project consumer.
2. The recorded hint.
3. The output of `gh config get git_protocol -h HOST`, when `gh` is on PATH. This is read-only, and no `gh` failure is fatal.
4. The other scheme.

For SSH, MASK uses the scp form (`git@H:P`), never the `/~/` URI. Every candidate runs with the existing noninteractive environment (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, `ssh -o BatchMode=yes`). Only an authentication or reachability failure moves to the next candidate. An endpoint rewrite, a redirect policy, an object-format mismatch or a content failure refuses immediately. If every candidate fails, the result is `git.auth_required` listing every attempted transport. A bare `update` over many consumers skips step 1 and fetches each tap once. `source show`, `doctor` and `--json` fetch results report `transport`, `transport_policy` and which step chose it.

**Cache and state.** The cache path is keyed by the canonical identity. On a tap machine, `mask doctor --migrate` converts a catalog entry, cache path, registered consumer records and link resolution rows whose identity is a non-canonical forge spelling, in one recoverable journal. An existing cache is reused when its marker names an equivalent identity. Otherwise the cache is left in place and refetched. `doctor` reports these rows as `migration.identity_canonicalization` and never rewrites project files. After migration, a machine approved over HTTPS and a machine approved over SSH both accept either committed spelling.

**Guarantees kept.** `endpoint` still refuses a Git `insteadOf` or `pushInsteadOf` rewrite whose normalized identity leaves the tap's identity. HTTPS redirect policy checks, credential refusal and `file://` identities are unchanged. Forge equivalence is never inferred from a project file, a lock or a remote's response.

## Out of scope

- Consumer integration-approval identities (`mask_ensure.repository_identity`).
- Installing or configuring credentials: `gh auth setup-git` and SSH keys remain the user's.
- Rewriting committed files on read.
- Hosts that serve different repositories over HTTPS and SSH under one name.
- Mirrors, fleet transport, and any new network protocol.

## Acceptance criteria

**RFC-MASK-0022-AC01** — **One identity per forge repository.** For a forge host, `https://H/O/R`, `https://H/O/R.git`, `ssh://git@H/O/R.git` and `git@H:O/R.git` normalize to `https://H/O/R.git`. A declaration committed with any of these spellings reaches `mask ensure` exit 0, with no file change, on fixture machines whose taps were added with each other spelling. `tests/test_sources.py` asserts this equality for forge hosts in place of the current inequality.

**RFC-MASK-0022-AC02** — **Strict elsewhere, opt-in on the machine.** For `example.test`, HTTPS and SSH identities stay distinct and a mismatch still fails `source.identity_mismatch`. Adding `example.test` to that machine's `forge_hosts` makes them equivalent. A `forge_hosts`-shaped field in a project declaration or lock is refused as invalid. An explicit `/~/` path, a non-`git` SSH user and a non-default port stay strict on forge hosts.

**RFC-MASK-0022-AC03** — **Transport follows convention without prompting.** Fixture scenarios (using local transports, shims or a fake `gh`) show:
- A project whose `origin` uses HTTPS fetches its derived tap over HTTPS, and an SSH origin fetches over SSH.
- Personal scope uses the `gh` protocol, then the hint, then the probe.
- A failed first candidate falls back to the next one and is reported.
- No prompt occurs, and a candidate never uses the `/~/` URI.
- `source show --json` reports the chosen transport, the policy and the step that chose it.

**RFC-MASK-0022-AC04** — **Pinning is explicit and machine-local.**
- `tap add --pin-transport` and `tap transport NAME URL` pin the transport, and a pinned tap never tries another candidate.
- `tap transport NAME --derive` unpins it.
- An URL with a different identity refuses `source.identity_mismatch` without effect.
- No pin or transport appears in `.mask.json` or `.mask.lock.json`.

**RFC-MASK-0022-AC05** — **Existing files and machines keep working.**
- Pre-RFC declarations and locks using HTTPS or `ssh://…/~/` forge spellings verify their recorded selection digests and deploy unchanged.
- `ensure` and `doctor` leave them byte-identical.
- The next `update` that writes the lock uses the canonical spelling with unchanged payload digests and commits.
- On a machine carrying a non-canonical identity in config and state, `doctor --migrate` converts the catalog, cache path, consumer records and link resolution rows. A crash at each journal checkpoint recovers with `recover --rollback` to the exact prior bytes, or with `--complete`.

**RFC-MASK-0022-AC06** — **Security boundaries hold.** A Git `insteadOf` rewrite to another identity, an effective HTTPS redirect policy, a credential-bearing URL and a transport whose fetched commit or payload digest differs from the lock all refuse, as today. Tests show that a derived transport cannot select a repository outside the equivalence class.

**RFC-MASK-0022-AC07** — **Truthful help, contract and suite.**
- `mask tap --help`, `mask source show --help`, README, the source guides and `docs/architecture/cli-contract.md` describe identity versus transport, the forge set and pinning.
- The schema documents `forge_hosts` and `transport_policy`.
- `python scripts/verify_documentation.py --root .` reports zero violations.
- The full `python -B -m unittest` suite passes.

**RFC-MASK-0022-AC08** — **Owner dogfood.** On the owner's ExampleOwnerHost machine and on a machine approved over SSH, with no hand edits to `MASK_HOME`, `mask ensure` exits 0 in both ExampleReview and ManageAgentSkills from the checked-in declarations. The transcripts are recorded in the closeout.

## Rollout and rollback

1. Land the normalizer and comparison sites behind the existing fixtures first, with AC01 and AC02 tests updated in the same change.
2. Land transport selection next, then pinning commands, then doctor canonicalization.
3. The previous program reads a canonical HTTPS spelling as it does today, so it continues to work for HTTPS-approved machines. It still refuses an SSH-approved machine against canonical files.
4. A `doctor --migrate` journal written by this program is refused by the previous one with `recovery.conflict`. Finish recovery before switching executables.
5. Rollback of a migrated machine is `recover --rollback` while the journal is pending. Afterwards, `tap transport NAME URL` restores a pinned transport. Nothing deletes caches, the store or checkouts.

## Risks stated plainly

- **The forge list is a trust assumption.** It is correct for the named hosts, where HTTPS and SSH front one repository namespace and one permission model. A self-hosted host added to `forge_hosts` by mistake could equate two different servers. That opt-in is the user's decision and is reported by `doctor`.
- **Paths keep their case.** GitHub treats owner and repository names case-insensitively, but MASK does not, so `MikeMarcin` and `mikemarcin` remain different identities.
- **Probing can add latency.** It adds at most one extra noninteractive connection per tap per fetch, and a working hint avoids it. `update` over many consumers ignores each consumer's origin, so a machine that authenticates only one way should pin or rely on the recorded hint.
- **Old locks keep old spellings.** Committed locks keep SSH spellings until their next write, so diffs in consumer repositories may show a one-time identity rewrite.

## Open questions for the owner

- **Canonical spelling:** `https://H/P.git` minimizes churn, but a scheme-free `H/P` would read as neutral. This RFC proposes the HTTPS spelling.
- **Forge list:** should the built-in set be only `github.com`, until another host is actually used?
- **Transport memory:** should a successful derived transport be remembered per consumer as well as per tap?

## Implementation notes

Decisions taken during implementation, each narrower than or different from the text above. The contract of record is [cli-contract.md](../architecture/cli-contract.md#taps-payloads-and-caches).

- **Open questions.** Canonical spelling is `https://H/P.git`. The built-in forge set is the four named hosts. A proven transport is remembered per tap, not per consumer.
- **`/~/` on a forge host is read as the scp form, not kept strict.** AC02 lists an explicit `/~/` path as strict, while AC05 requires pre-RFC `ssh://…/~/` files to deploy unchanged. Both cannot hold: `ssh://git@H/~/P` is exactly what MASK recorded for `git@H:P` before this RFC, and no forge serves a home-relative path, so that spelling can only be MASK's own older output. It folds to the forge identity everywhere. A non-`git` user and a non-default port stay strict.
- **Candidate order.** The Decision, the Contract list and AC03 order `gh` and the hint differently. Implemented: origin; a transport a fetch *proved*; `gh`; the URL typed at `tap add` (unproven); the other scheme. A proven hint outranks a stated preference, and an unproven one does not, which satisfies AC03's personal-scope order on a fresh machine and the Contract's order afterwards.
- **The hint lives beside the cache, not in `config.json`.** Fetches run inside journaled operations that bind the configuration's bytes; rewriting `transport` mid-operation would turn a successful fetch into a `recovery.conflict`. `mask-transport.json` in the tap's cache records it, and `source show` reports it. `config.json`'s `transport` is the typed or pinned URL.
- **`doctor --migrate` converts the catalog only, in one atomic write without a journal.** Project files are never rewritten for a spelling, and a consumer's state records mirror those files, so converting state would only make it disagree with the lock it describes; state takes the canonical spelling when its files are next written. The cache is reused in place under its existing key, which `cache_root` accepts for any spelling of the same identity, so there is no directory move to journal. One atomic replace leaves the old bytes or the new, so there are no journal checkpoints to crash at; AC05's crash-recovery clause has nothing to exercise.
- **`forge_hosts` is set with `mask config set --forge-host HOST` / `--clear-forge-hosts`**, since editing `MASK_HOME` by hand is not a supported path.

## Closeout

Exactly one linked closeout card records every criterion, actual command or observation, outcome and implementation revision. Missing native or owner dogfood evidence keeps the closeout open. Filing, fixture success and documentation edits are not acceptance.
