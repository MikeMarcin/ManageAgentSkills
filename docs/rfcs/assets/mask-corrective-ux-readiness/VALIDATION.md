# Actual pack checks and baseline observation

## Checks run in this environment

Environment: Linux, Python 3.13.5. These are pack checks and disposable source
reproductions, not native macOS/Windows qualification or implementation of the RFCs.

| Check | Actual result |
|---|---|
| `python3 -B tools/validate_pack.py --jsonschema` | Passed: two proposed RFCs, twelve provisional cards, sixteen criteria, zero pack violations; proposed schema and both package examples validated |
| `python3 -B -m unittest discover -s tools -p 'test_pack.py' -v` | Eleven tests passed, including duplicate/cyclic/missing-reference, path/digest/producer guards and the explicit synthetic staging fixture |
| Supplied AgentSkills `board_model.parse_matter` and canonical issue-card JSON schema | All twelve card frontmatters accepted; both RFC frontmatters parsed with Proposed status |
| Disposable old-source public CLI reproduction | Observed JSON without --json and successful link-only ensure/check while both required integrator role outputs were absent |

The final manifest is rehashed and pack validation repeated after this record is
written. It binds every deliverable file except the manifest itself. Final archive
integrity is additionally checked after ZIP creation.

## Reproduced old behavior

`tools/reproduce_supplied_baseline.py` ran the uploaded MASK program snapshot in
new temporary Git/source/consumer/MASK_HOME directories, using only public MASK
commands. It did not edit the user's repositories or machine configuration.
The normalized result is `fixtures/supplied-baseline-observation.json`.

Observed: inventory without --json returned parseable JSON with six link rows;
ensure and ensure --check both exited 0 with ready_legacy_unpinned; neither
`.codex/agents/rfc-integrator.toml` nor `.claude/agents/rfc-integrator.md` existed.
No package setup script or provider/model session ran. The proposed workflow
sidecar was passive data unknown to the old implementation, illustrating why a
new sidecar alone cannot make an older program enforce readiness.

This fixture intentionally prepares an existing broken installation so that its
old ensure path can be observed. It is not the future fresh-install acceptance
journey, and it is not another measurement of the actual SRV session. Runtime
claims about the new implementation remain entirely pending.

## Not performed or claimed

No product changes, live ID reservation, user-terminal/native macOS or Windows
qualification, actual AgentSkills staging handoff, provider role loading, live
consumer migration, permission/credential changes, Git publication or quota
improvement. The included golden outputs and replacement README are target
specimens. Pack integrity is not a PASS on any product acceptance criterion.
