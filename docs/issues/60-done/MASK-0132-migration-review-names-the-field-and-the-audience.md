---
schema: "implement-rfc.card.v1"
id: "MASK-0132"
title: "Make the migration review name the changed field and only warn about files for persisted schemas"
status: "Done"
rfcs: []
depends_on: ["MASK-0131"]
priority: "P2"
metadata: {"origin":"Owner run of mask update 4ca5508 -> d7407ca on bpr-linux (2026-10-03)"}
acceptance: [{"criterion":"MASK-0132-AC1","outcome":"pass","revision":"5c97bfbfc0b22776489acfee4cf53c3dd338088a","evidence":{"kind":"command","detail":"program_migration on the real repo 4ca5508..d7407ca gives result.schema.json breaking 'now constrains data.commits' audience output; tests.test_launcher test_output_only_breaking_change_names_the_field_and_spares_files asserts the same summary on a fixture"}},{"criterion":"MASK-0132-AC2","outcome":"pass","revision":"5c97bfbfc0b22776489acfee4cf53c3dd338088a","evidence":{"kind":"command","detail":"Same test: output-only breaking refusal prints the output-only sentence and not the files warning; adding a persisted machine-v3 breaking row restores the files warning"}},{"criterion":"MASK-0132-AC3","outcome":"pass","revision":"5c97bfbfc0b22776489acfee4cf53c3dd338088a","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_launcher tests.test_human_output tests.test_consent tests.test_update tests.test_cli_protocol: 61 OK; JSON rows carry audience files|output"}}]
---

# MASK-0132: Make the migration review name the changed field and only warn about files for persisted schemas

## Evidence

The first real use of the MASK-0131 review printed:

```
    result.schema.json   breaking   adds properties at data
  Some existing files may no longer validate with this version.
```

The change typed `data.commits` (from `mask upgrade --commit`, MASK-0129) on a `data` object that used to accept anything. Calling that `breaking` is correct, because a constrained property on an open object narrows it. The output had two problems:

- "adds properties at data" names a JSON Schema keyword, not the field. The reader can't tell what changed.
- `result.schema.json` describes MASK's own command output, which no saved file is validated against. Warning that existing files may stop validating was false, and it made a routine update look dangerous.

## Bounded work

1. When the classifier sees a new constraint keyword, the summary names its subject:
   - new `properties`: `now constrains data.commits` (and `N more` past two)
   - new `required`: `now requires X`
   - any other keyword: `adds a KEY rule to PATH`
2. Each schema row carries `audience`:
   - `output` for `result.schema.json`, which describes command output
   - `files` for every other schema
3. The review and refusal text depends on the breaking rows:
   - If any breaking row has audience `files`: `Some existing files may no longer validate with this version.`
   - If every breaking row has audience `output`: `Only MASK's --json output changes shape; your files are unaffected.`

   The classes, consent requirement and plan hash don't change.

## Acceptance

- **MASK-0132-AC1:** A new constrained property on an open object is classified `breaking` with the summary `now constrains PATH`. The 4ca5508 -> d7407ca change gives `result.schema.json breaking now constrains data.commits`.
- **MASK-0132-AC2:** A breaking change only to `result.schema.json` prints the output-only sentence and not the files warning. A breaking change to a persisted schema still prints the files warning.
- **MASK-0132-AC3:** Rows include `audience` in JSON. The existing MASK-0131 launcher tests still pass.
