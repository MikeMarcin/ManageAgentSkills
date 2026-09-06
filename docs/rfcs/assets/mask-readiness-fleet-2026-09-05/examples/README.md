# Synthetic contract examples

**No example is a live installation, receipt, signature, enrolled machine or successful native check.** The remote URL uses `example.invalid` and is intentionally non-routable. Do not execute these against real devices.

`fixture-source` contains ordinary synthetic skill files. The local fixture Git commit `efeff6d2bda88a7d4e09028bedb3c6c7eefff758` was generated from those files during packet creation, without network access; it is not a revision of AgentSkills or MASK. The payload and metadata digests in the examples are computed from these fixture bytes. The .git directory is not distributed.

`project/.mask.json` selects all supported agents by default. `personal/selection.json` selects the same alpha skill only for Claude. This demonstrates independent per-skill/per-scope intent. `mac-notes` advertises a specific agent/platform and is explicitly conditional in the portable project selection.

The lockfiles demonstrate exact content identities, not live source availability. `fleet-intent.payload.json` and `device-receipt.payload.json` are **unsigned payloads**; they must not be accepted as authorized protocol requests. A production envelope must contain a verified signature from an enrolled authority.

`fleet-report.json` and `fleet-report.html` show an intentionally incomplete 2-of-3-device rollout. `complete=false`, `installed_everywhere=false`, and a nonzero incomplete result remain true despite successful devices. No outcome in these files is product acceptance evidence.

The four schemas under `../contracts` are proposed portable wire shapes, not shipped runtime files. Runtime semantic validation also checks trust, URI/path containment, ID uniqueness, source/lock coherence, platform policy and object identity.
