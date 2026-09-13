# Source basis and limits

The pack is drafted from a direct inspection of the live ManageAgentSkills
checkout at commit `d3e417478809e096be9cff155e38c7620d14ee71` (branch `main`,
clean worktree, NEXT_ID `MASK-0098`, 19 RFCs, 97 cards) and from the owner's
statements in the 2026-09-12 conversation. It is not a claim about any other
revision. No outside documentation overrides those sources.

| Inspected file | Lines | SHA-256 at the baseline |
|---|---|---|
| `mask.py` | 788 | `7e4dfb4469b1be1c74f7bcb57f815a581615cb196f381e2987e82fc8b8251111` |
| `mask_core.py` | 746 | `5ae6d5cfdeb6211e5295223dd9b632496a77a892da93f639675f2a5c2974c4ab` |
| `mask_fs.py` | 860 | `980aa1f8a2ece7717a3588c755ff4c59dd2e97185a424c6d7c720742d54df999` |
| `mask_pinned.py` | 785 | `784a7c7dfd2d4705965a59c804eb75021a07763e8286a1745b249f0e7e1d653b` |
| `mask_sources.py` | 847 | `8c6bd4ca84a2fbea9a5ff34e1f9c1bb74147e46b789153b67ac2c4af35e89e47` |
| `mask_task.py` | 374 | `cb26e1b27aad81653d18cb1fc6bcda282f5766da614ece7c35e2f65a145b3d6e` |
| `mask_git.py` | 286 | `4beae65ca16d10291b1af9989a2050bbcd800053f76d5b909fc4f411cea27a5b` |
| `mask_store.py` | 269 | `dfc9d968293ee1bbcc2df068a667b75f6c2ee2fd9dab387b56f84e28ad281377` |
| `mask_resolve.py` | 466 | `e2127eb7dd11f91d2fe0b034f912bcf7f7b862f7ace5eff8ac9444dad16ff92d` |
| `schemas/machine-v1.schema.json` | 57 | `1a4edbe2d474d4bb3640ced4e1b095fd6906661b3e2c5d88290bfb857276abef` |
| `schemas/machine-v2.schema.json` | 113 | `3e2ef4370d4b01516e089901133602f7bbb5121f7b1fe5f1008263d08e70bf12` |
| `README.md` | 128 | `95b3161aaae8cef30c536da9bb5b845e45c7bb53048b4e0621d635a8f05c6a73` |
| `docs/guides/installation.md` | 47 | `3b9ca5bbd1875c80f843c7aec5f2cfc93d211eea9988e7d397488199f6f7d376` |
| `docs/guides/sources-and-updates.md` | 87 | `d7a4f6afbae19909724c89065e643ea66885a4c6924e236c484244e04985ce2c` |
| `tests/support.py` | 62 | `fbdf7e7194bca41f3629f2928f92b362fb74fd9dadb70e7722ba6079ca6eaf39` |
| `tests/public_support.py` | 165 | `3f9be56615212e5e2b54a5a013879045109d2d4b2810c7d4fb73256f1f821d54` |
| `scripts/qualify_real_package.py` | 377 | `f04ca71b6f7c1b72fb55f4e2da59d3750208bb38eccbd03cea2bd4ef97d7e876` |

## Observed source facts

| Fact | Direct source location | Implication |
|---|---|---|
| `init` accepts only `--source PATH` and records it as `config.source.root` | `mask.py:50` (command table) and `mask.py:524-548` | There is no URL-only bootstrap; a local clone is mandatory |
| Legacy links target `<clone>/skills/<id>` | `mask_fs.py:127` (`creation_link_text(source / 'skills' / identifier)`), `mask_pinned.py:55` | Editing the clone edits every consumer; consumers are not pinned |
| Machine config v2 still requires the v1 `source` block and `legacy_source` | `schemas/machine-v2.schema.json` required list; `mask_sources.py:126` (`authoring != source.root` refusal) | The tap catalog cannot exist without a local clone |
| New consumers on a v1 machine are legacy | `mask_task.py:67` (`fresh_declaration`) | Every fresh `install` on the owner's machine links the clone |
| Pinned `update` resolves from cache only | `mask_pinned.py:619` (`resolve_candidate(..., refresh=True)`) with no fetch in `transition_dispatch` | Updates require a separate `source fetch` first |
| Unqualified `update` fast-forwards the user's clone | `mask_git.py:178-258` (`update`) | A MASK command mutates the user's authoring checkout |
| Basename identity check against the literal `AgentSkills` | `mask.py:575`, `mask_git.py:189`, `:207`, `:240`, `:267` | AgentSkills is special-cased instead of being an ordinary tap |
| README describes linking from one local checkout | `README.md:5` | Documentation presents the defect as the product |
| Test fixtures bootstrap with `init --source` | `tests/support.py:51-52`, `tests/public_support.py`, `scripts/qualify_real_package.py:120`, `:159` | The suite qualifies the legacy path; a tap-first suite does not exist |
| Managed cache, store, lock and resolver exist and work for v2 consumers | `mask_sources.fetch` (`:250-300`), `mask_store.location` (`:18-24`), `mask_task.v2_proposal` (`:170-225`) | The correction is a bootstrap and retirement change, not a new engine |

## The owner's machine

`~/.mask/config.json` at authoring time: `schema_version` 1, `source.root`
`C:\code\git\AgentSkills`, `remote` `origin`, `branch` `main`, `default_targets`
`["claude", "codex"]`, `git_timeout_seconds` 30. `state.json` has `projects: {}`
and no user record. No real consumer is registered, so the owner migration is a
configuration-only migration followed by a fresh personal install.

## Owner decisions versus proposed mechanics

**Owner-required outcomes (2026-09-12):** retire the live-checkout mode
entirely; `mask update` fetches every referenced tap and then re-resolves;
existing v1 machines, projects and personal installs are migrated by `mask
doctor` (or a closely related form); deliver the change as a corrective RFC pack
that the implement-rfc workflow can import and implement.

**Proposed mechanics in this pack:** machine config v3, `tap add` bootstrap,
`init` without `--source`, a fetching and tap-isolating `update`, `doctor
--migrate` with acquisition from the local clone over file transport, and the
retirement inventory in CHANGE_MAP.md. These are implementation proposals;
`project/user set|require|unrequire` are retained for v2 declarations by the
pack author's judgment, not by an owner directive.

No live IDs, implementation baseline SHA, native PASS, real machine migration or
transcript is invented. The baseline observations above were read from the
source; none were produced by running MASK against the owner's configuration.
