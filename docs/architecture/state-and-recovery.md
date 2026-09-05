# Local state and recovery data

The public API is the CLI, not these internal files. The following is the v1 serialization contract to implement and schema-test. No agent should hand-edit it during ordinary management.

## config.json

See `templates/schemas/machine.schema.json` in the original packet. The program root is not the configured skill source. Both are discovered/reported independently. Source replacement is refused once initialized; defaults/timeouts have dedicated CLI edits.

## state.json

```json
{
  "schema_version": 1,
  "generation": 1,
  "projects": {
    "/example/project": {
      "root": "/example/project",
      "root_identity": {"device": 1, "inode": 123},
      "last_manifest": {"schema_version": 1, "skills": ["implement-rfc"], "targets": ["claude", "codex"]},
      "last_manifest_digest": "sha256:<computed-digest>",
      "last_source_revision": null,
      "links": {
        ".claude/skills/implement-rfc": {
          "skill": "implement-rfc",
          "target": "claude",
          "link_text": "/example/AgentSkills/skills/implement-rfc"
        }
      }
    }
  },
  "launchers": {}
}
```

Example values are not real host identities or evidence. Store last_source_revision only when known; it is observational, not a project lockfile. The root identity is an available-platform consistency check, not a globally stable UUID or proof of ownership. Handle unavailable/unstable platform identity explicitly and never infer a replacement directory is owned because it occupies the same path.

Validate each projects key against its canonical root; recompute each relative link path from its target and skill. The on-disk symlink's current raw link value must still agree before unlink. Derive current desired links from the **live manifest**, never the last_manifest cache. Unavailable projects are reported and block whole-source update; last_manifest is diagnostic only.

Do not increment generation or rewrite last-observed fields for a true no-op. Store only meaningful changed observations as part of successful explicit mutations. Read-only inspections do not rewrite caches. `launchers` is a small path-to-owned-launcher record with program root, interpreter path and prior content digest; it is not an executable command list loaded from a project.

## pending.json

Required fields: schema_version, transaction_id, operation, phase, base_generation, selected canonical projects, expected before/after manifest text where relevant, before/after link values and intended state changes. Source/program updates additionally record the applicable checkout root and before/candidate/observed-after commits. The journal never contains credentials, script bodies to execute, arbitrary command lines or a copy of source history.

Before-state includes whether each leaf was absent or the exact previous owned link. After-state includes the intended new value/absence. Operation markers are written before effects and progress can be refined afterward. Recovery validates whole intent against the fixed adapters, selected registered roots and current filesystem; no journal path is blindly trusted.

A link created immediately before process death may exist before a completion marker was saved. Recovery uses the bounded creation intent plus unchanged planned value, under the cooperative-writer/OS-lock model, to complete or roll back only that operation. A hostile same-user process can forge state or recreate an identical path; MASK does not claim to defeat that adversary.

If an existing file/directory or mismatching symlink appears, recovery refuses and preserves it. Recreate an old link only in an absent destination. Restore manifest text only when current bytes still match the expected operation state. Preserve a journal whenever safe completion cannot be established. Program/source Git checkouts are never automatically reset by recovery.

## Failure boundaries to inject

Test process exit after intent write; after first link creation; after one owned unlink; after manifest replacement but before state; after state replacement but before journal cleanup; after Git HEAD advance but before project effects; after parent/leaf replacement by a cooperative external writer. Check both recovery completion and rollback where supported. Do not claim operating-system power-loss durability from an exception-injection test.

Once implementation chooses the precise journal layout, publish its strict internal JSON schema beside the state schema and test migrations/refusals. This does not add a second database or an externally editable command format.
