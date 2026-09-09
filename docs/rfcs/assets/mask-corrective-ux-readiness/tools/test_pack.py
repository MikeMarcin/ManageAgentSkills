"""Focused pack guard tests, not acceptance tests for the future MASK implementation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import validate_pack as v

class PackTests(unittest.TestCase):
    def test_structure_is_valid(self):
        self.assertEqual(v.validate_structure(v.ROOT), [])

    def test_cycle_is_detected(self):
        plan = v.read_json(v.ROOT/'issue-plan.json')
        plan['cards'][0]['depends_on']=['MASK-0084']
        self.assertTrue(any('cycle' in e for e in v.validate_plan(plan)))

    def test_missing_dependency_is_detected(self):
        plan = v.read_json(v.ROOT/'issue-plan.json')
        plan['cards'][1]['depends_on']=['MASK-9999']
        self.assertIn('missing dependency MASK-9999',v.validate_plan(plan))

    def test_duplicate_role_is_detected(self):
        pkg=v.ROOT/'fixtures/static-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['native_roles'].append(copy.deepcopy(doc['native_roles'][0]))
        self.assertIn('duplicate native role',v.validate_workflow(pkg,doc))

    def test_traversing_asset_is_detected(self):
        pkg=v.ROOT/'fixtures/static-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['native_roles'][0]['asset']['path']='../elsewhere.toml'
        self.assertIn('unsafe asset path',v.validate_workflow(pkg,doc))

    def test_asset_digest_mismatch_is_detected(self):
        pkg=v.ROOT/'fixtures/static-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['native_roles'][0]['asset']['sha256']='0'*64
        self.assertIn('role asset hash mismatch',v.validate_workflow(pkg,doc))

    def test_two_producers_are_rejected(self):
        pkg=v.ROOT/'fixtures/static-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['native_roles'][0]['setup']='x'
        self.assertIn('role must have exactly one producer',v.validate_workflow(pkg,doc))

    def test_unknown_setup_is_detected(self):
        pkg=v.ROOT/'fixtures/generated-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['native_roles'][0]['setup']='undeclared'
        self.assertIn('undeclared setup action',v.validate_workflow(pkg,doc))

    def test_setup_entrypoint_is_in_staleness_inputs(self):
        pkg=v.ROOT/'fixtures/generated-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['setup'][0]['package_inputs']=[]
        self.assertIn('entrypoint absent from package inputs',v.validate_workflow(pkg,doc))

    def test_setup_unknown_consumer_input_is_rejected(self):
        pkg=v.ROOT/'fixtures/generated-package'
        doc=v.read_json(pkg/'mask-workflow.json')
        doc['setup'][0]['inputs'].append('unknown')
        self.assertIn('unknown consumer input',v.validate_workflow(pkg,doc))

    def test_setup_fixture_stages_without_consumer_writes(self):
        # Explicit execution of a synthetic test-only producer, not package install.
        with tempfile.TemporaryDirectory(prefix='mask-pack-stage-') as temp:
            stage=Path(temp)/'stage';stage.mkdir()
            consumer=v.ROOT/'fixtures/consumer'
            before={p.relative_to(consumer):p.read_bytes() for p in consumer.rglob('*') if p.is_file()}
            argv=[sys.executable,'-B',str(v.ROOT/'fixtures/generated-package/scripts/prepare_fixture_roles.py'),
                  '--repo-root',str(consumer),'--output-root',str(stage),
                  '--request-file',str(v.ROOT/'fixtures/setup-request.example.json')]
            run=subprocess.run(argv,capture_output=True,text=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual({p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()},
                             {'codex/rfc-integrator.toml','claude/rfc-integrator.md'})
            after={p.relative_to(consumer):p.read_bytes() for p in consumer.rglob('*') if p.is_file()}
            self.assertEqual(before,after)
            rerun=subprocess.run(argv,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(rerun.returncode,0)

if __name__=='__main__': unittest.main()
