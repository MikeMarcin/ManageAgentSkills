# Fixed setup interface details

Normative adjunct for the first staged Python action, not a general shell format.

`python -B ENTRYPOINT --repo-root CONSUMER --output-root STAGE --request-file REQUEST`
uses the already selected MASK interpreter. Every value is a separate argv
argument, not interpolated command text. The request file is UTF-8 JSON:

```json
{
  "schema": "mask.setup-request.v1",
  "action": "prepare-roles",
  "native_roles": [{"agent": "codex", "name": "rfc-integrator"}],
  "inputs": [{"id": "project-config", "path": ".mask/skill-config/implement-rfc/project.json", "sha256": "<actual current digest>"}],
  "parameters": {}
}
```

The digest placeholder above is explanatory, not a valid fixture. Runtime
requires actual bounded digests and derives request contents from the frozen
proposal. Action identifiers in noninteractive approval are source-qualified:
`SOURCE/ID:ACTION`; request.action is only the action within that selected package.

Each requested role produces exactly `STAGE/AGENT/NAME.toml` for Codex or
`STAGE/AGENT/NAME.md` for Claude. No other output file, link, or directory tree is
admitted. Stage path spelling is distinct from the final native destination,
which only MASK's adapter derives. Standard output is bounded diagnostic text,
not a command stream, approval, or authority to add roles. Exit 0 only means the
producer reports completion; MASK validates all outputs and current inputs.

Descriptor setup.package_inputs names the role-relevant package files that
invalidate an already prepared role lock, and must include the entrypoint.
setup.inputs refers to top-level consumer-input IDs. Missing/duplicate/escaping
or unknown references are refused. The publisher's generator must depend only
on those declared inputs for its output; equivalence tests pin this boundary.
Full package bytes, selected descriptor, and interpreter identity are still
bound for execution consent, even if only a subset affects role staleness.

A generated consumer role lock is a closed portable object with schema
`mask.native-role-lock.v1`, source-qualified coordinate, workflow-contract digest,
role-input digest, parameter digest, bounded consumer input ID/path/hash entries,
and exact output agent/name/hash entries. It contains no absolute machine paths,
execution permission, credential, or arbitrary destination. A missing optional
input is represented explicitly rather than hashing the bytes of an empty file.
The selected contract determines the required set; the lock cannot omit a role
or add authority. MASK computes a lock after validated staged output; authoring
can produce the same portable form for checked-in files.

The pack's generated fixture omits the real consumer renderer and never writes
final destinations. Its tests demonstrate only this request/staging shape.
