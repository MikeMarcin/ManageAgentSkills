import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import mask
import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_resolve as r
import mask_store as store
from tests.support import Fixture, ENTRY, TAP


class PinnedTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source','fetch',TAP)
        self.declaration=dict(schema_version=2,sources=self.binding(),skills=[dict(source=TAP,id='alpha')])
        (self.project/'.mask.json').write_text(json.dumps(self.declaration))
        self.lock=self.call('lock')['data']['lock']
        self.row=self.lock['packages'][0]
        self.config=c.config(c.read_json(self.home/'config.json'))

    def register(self, apply=False):
        return self.call('project','register','--project',self.project,*(['--apply'] if apply else []))

    def crash(self,label,command=None):
        script="""
import os,sys
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[2] else None
mask.main(sys.argv[3:])
"""
        run=subprocess.run([sys.executable,'-B','-c',script,str(ENTRY.parent),label,*(command or ['apply']),'--project',str(self.project),'--home',str(self.home),'--json'],capture_output=True,text=True)
        self.assertEqual(run.returncode,99,run.stdout+run.stderr)

    def test_public_two_worktrees_raw_versions_and_warm_noop(self):
        self.register()
        preview=self.call('apply','--dry-run')
        before=self.snapshot()
        self.assertTrue(preview['would_change'])
        self.assertEqual(before,self.snapshot())
        self.call('apply','--expect-plan-hash',preview['data']['plan_hash'])
        old=os.readlink(self.project/'.agents/skills/alpha')
        self.git(self.project,'config','user.name','Fixture')
        self.git(self.project,'config','user.email','fixture@example.invalid')
        self.git(self.project,'add','.mask.json','.mask.lock.json')
        self.git(self.project,'commit','-m','pin first')
        other=self.base/'other-worktree'
        self.git(self.project,'worktree','add','-b','other',str(other))
        (self.source/'skills/alpha/version').write_bytes(b'new version\r\n')
        self.publish('second version')
        self.call('source','fetch',TAP)
        self.call('lock','--project',other,'--refresh')
        self.call('project','register','--project',other,'--apply')
        self.assertNotEqual(old,os.readlink(other/'.agents/skills/alpha'))
        self.assertEqual(old,os.readlink(self.project/'.agents/skills/alpha'))
        self.assertEqual(self.call('lock','--refresh',code=4)['error']['code'],'lock.active')
        before=self.snapshot()
        self.assertFalse(self.call('apply')['changed'])
        self.assertEqual(before,self.snapshot())
        self.assertTrue(self.call('doctor','--project',self.project,'--check')['data']['healthy'])
        self.assertEqual(self.call('project','show')['data']['mode'],'pinned')
        inventory=self.call('inventory')['data']
        self.assertTrue(inventory['complete'])
        self.assertEqual(inventory['consumers'][0]['mode'],'pinned')
        self.assertTrue(inventory['rows'])
        self.assertEqual({row['status'] for row in inventory['rows']},{'managed_converged'})

    def legacy_record(self,name,skills):
        """A mode-less consumer record beside pinned ones, written straight into state with its v1 declaration and links; no legacy command runs."""
        from tests.legacy_support import create_links,legacy_record,write_json
        root=self.base/name;root.mkdir()
        declaration,record=legacy_record(SimpleNamespace(clone=self.source),root,skills)
        write_json(root/'.mask.json',declaration)
        create_links(root,record)
        state=c.read_json(self.home/'state.json',default=c.empty_state())
        state['projects'][str(root)]=record
        write_json(self.home/'state.json',state)
        return root,record

    def test_personal_scope_preserves_legacy_records_and_state3(self):
        from tests.legacy_support import snapshot
        legacy,original=self.legacy_record('legacy-project',['beta'])
        files=snapshot(self.base,legacy)
        self.register(True)
        user=self.base/'user-home';user.mkdir()
        (self.home/'user.json').write_text(json.dumps(self.declaration))
        self.call('lock','--user')
        self.call('user','register','--user-home',user,'--apply')
        state=c.state(c.read_json(self.home/'state.json'))
        self.assertEqual(state['schema_version'],3)
        self.assertEqual(c.text_json(state['projects'][str(legacy)]),c.text_json(original))
        self.assertEqual(state['user']['mode'],'pinned')
        self.call('user','unregister')
        state=c.read_json(self.home/'state.json')
        self.assertEqual(state['schema_version'],3)
        self.assertEqual(c.text_json(state['projects'][str(legacy)]),c.text_json(original))
        self.assertEqual(snapshot(self.base,legacy),files)
        self.assertTrue((self.project/'.agents/skills/alpha').is_symlink())

    def test_readiness_exact_authority_and_no_inferred_network(self):
        # Events need approval first; manual JSON readiness gets a typed one-time proposal instead (MASK-0085).
        self.assertEqual(self.call('ensure','--event','startup',code=4)['error']['code'],'integration.approval_required')
        refused=self.call('ensure',code=4)
        self.assertEqual(refused['error']['code'],'confirmation.required')
        self.assertEqual(refused['data']['confirmation']['reason'],'integration.approval_required')
        self.call('integration','approve','--project',self.project)
        before=self.snapshot()
        self.call('ensure','--check',code=7)
        self.assertEqual(before,self.snapshot())
        ready=self.call('ensure','--offline')
        self.assertEqual(ready['data']['readiness'],'ready_pinned')
        self.assertFalse(self.call('ensure')['changed'])
        self.call('integration','approve','--project',self.project,'--allow-locked-fetch',TAP)
        self.call('integration','approve','--project',self.project)
        self.assertEqual(c.read_json(self.home/'integration.json')['approvals'][str(self.project)]['allow_locked_fetch'],[TAP])
        altered=copy.deepcopy(self.declaration);altered['skills'][0]['when']={'platforms':['windows']}
        (self.project/'.mask.json').write_text(json.dumps(altered))
        (self.project/'.mask.lock.json').write_text(c.text_json(dict(self.lock,selection_digest=r.selection_digest(altered))))
        result = self.call('ensure')
        import mask_selection as selection
        expected = 'deployed' if selection.device()['platform'] == 'windows' else 'not_applicable'
        self.assertEqual(result['data']['outcomes'][0]['status'], expected)

    def test_preparation_outside_writer_and_generation_cas(self):
        self.register()
        original=store.ensure
        def changed(*args,**kwargs):
            with c.writer_lock(self.home):
                before=c.state(c.read_json(self.home/'state.json'))
                after=copy.deepcopy(before)
                after['generation']+=1
                c.atomic_text(self.home/'state.json',c.text_json(after),c.read_text(self.home/'state.json'))
            return original(*args,**kwargs)
        parser,leaves=mask.make_parser();args=parser.parse_args(['apply','--project',str(self.project),'--home',str(self.home)])
        output=mask.result('apply')
        with patch.object(store,'ensure',side_effect=changed),self.assertRaises(c.MaskError) as error:
            mask.dispatch(args,output,leaves)
        self.assertEqual(error.exception.code,'plan.stale')
        self.assertFalse((self.project/'.agents/skills/alpha').is_symlink())
        self.assertFalse((self.home/'pending.json').exists())
        self.assertTrue(output['changed'])
        self.assertEqual(output['transaction'],'not_started') # MASK-0110: retained preparation is not a consumer transaction.
        self.assertTrue(output['data']['preparation'][0]['effects']['artifacts'][0]['created'])
        self.assertEqual(output['data']['retained_preparation']['artifacts'],[output['data']['preparation'][0]['effects']['artifacts'][0]['path']])

    def test_crash_intent_link_state_complete_and_rollback(self):
        self.register()
        for label in ('intent','link','state'):
            with self.subTest(label=label):
                self.crash(label)
                self.call('recover','--inspect')
                self.call('recover','--rollback')
                self.assertFalse((self.project/'.agents/skills/alpha').is_symlink())
                self.crash(label)
                self.call('recover','--complete')
                self.assertFalse(self.call('apply')['changed'])
                self.call('project','unregister')
                self.register()

    def test_typed_lock_transition_retarget_and_tamper(self):
        self.register(True)
        before_state=c.state(c.read_json(self.home/'state.json'))
        (self.source/'skills/alpha/next').write_text('next')
        self.publish('next')
        self.call('source','fetch',TAP)
        candidate=r.resolve_candidate(self.declaration,self.config,self.home,self.lock,refresh=True)
        store.ensure(self.home,self.declaration,candidate,self.config)
        planned=fs.plan(self.config,before_state,[self.project],home=self.home,lock_proposals={str(self.project):candidate})
        fs.ensure_applicable(planned)
        pending=fs.make_pending(planned,self.home)
        fs.validate_pending(pending,self.home)
        bad=copy.deepcopy(pending);bad['files'][0]['role']='user_lock'
        with self.assertRaises(c.MaskError):fs.validate_pending(bad,self.home)
        for field in ('files','links'):
            with self.subTest(stripped=field):
                bad=copy.deepcopy(pending);bad[field]=[]
                with self.assertRaises(c.MaskError) as error:fs.check_current(bad,self.home)
                self.assertEqual(error.exception.code,'recovery.conflict')
                (self.home/'pending.json').write_bytes(c.text_json(bad).encode('utf-8'))
                before=self.snapshot()
                self.call('recover','--complete',code=8)
                self.assertEqual(before,self.snapshot())
                (self.home/'pending.json').unlink()
        output=mask.result('apply');fs.public_plan(planned,output)
        with patch.object(fs,'checkpoint',side_effect=lambda label: (_ for _ in ()).throw(KeyboardInterrupt()) if label=='lock' else None),self.assertRaises(KeyboardInterrupt):
            fs.execute(planned,self.home,output)
        self.assertEqual(json.loads((self.project/'.mask.lock.json').read_text()),self.lock)
        fs.execute(planned,self.home,mask.result('apply'))
        self.assertEqual(json.loads((self.project/'.mask.lock.json').read_text()),candidate)
        self.assertEqual(fs.normalized_link(self.project/'.agents/skills/alpha',os.readlink(self.project/'.agents/skills/alpha')),store.location(self.home,candidate['packages'][0]['payload_digest'],'alpha')[1])

    def test_recovery_refuses_branch_control_and_old_artifact_corruption(self):
        self.register()
        self.crash('link')
        original=(self.project/'.mask.lock.json').read_bytes()
        (self.project/'.mask.lock.json').write_bytes(original+b' ')
        self.call('recover','--complete',code=8)
        (self.project/'.mask.lock.json').write_bytes(original)
        root,target=store.location(self.home,self.row['payload_digest'],'alpha')
        leaf=target/'SKILL.md';leaf.chmod(0o644);raw=leaf.read_bytes();leaf.write_bytes(b'broken')
        self.call('recover','--rollback',code=8)
        leaf.write_bytes(raw);leaf.chmod(0o444)
        self.call('recover','--rollback')

    def test_adopt_relative_pinned_link_preserves_spelling(self):
        self.register()
        self.call('source','fetch','--locked','--offline')
        target=store.location(self.home,self.row['payload_digest'],'alpha')[1]
        leaf=self.project/'.agents/skills/alpha';leaf.parent.mkdir(parents=True)
        raw=os.path.relpath(target,leaf.parent);leaf.symlink_to(raw,target_is_directory=True)
        adopt=('link','adopt','--project',self.project,'--skill','alpha','--target','codex','--expect-source',target)
        before=self.snapshot()
        preview=self.call(*adopt,'--dry-run')
        self.assertEqual(before,self.snapshot())
        self.assertEqual(self.call(*adopt,'--expect-plan-hash','sha256:'+'0'*64,code=4)['error']['code'],'plan.stale')
        self.assertEqual(before,self.snapshot())
        self.call(*adopt,'--expect-plan-hash',preview['data']['plan_hash'])
        self.assertEqual(os.readlink(leaf),raw)
        self.call('apply')
        self.assertEqual(os.readlink(leaf),raw)

    def test_public_hydration_needs_exact_scope_grant_and_retains_old_lock(self):
        cache=Path(self.config['sources'][TAP]['cache'])
        cache.rename(self.base/'retained-cache')
        (self.source/'skills/alpha/new').write_text('upstream moved')
        newer=self.publish('new upstream')
        original=(self.project/'.mask.lock.json').read_bytes()
        self.call('integration','approve','--project',self.project)
        before=self.snapshot()
        self.assertEqual(self.call('ensure',code=4)['error']['code'],'artifact.unavailable')
        self.assertEqual(before,self.snapshot())
        self.call('integration','approve','--project',self.project,'--allow-locked-fetch',TAP)
        before=self.snapshot()
        self.assertEqual(self.call('ensure','--offline',code=4)['error']['code'],'artifact.unavailable')
        self.assertEqual(before,self.snapshot())
        ready=self.call('ensure')
        self.assertEqual(ready['data']['network'],'locked_fetch')
        effects=ready['data']['preparation'][0]['effects']
        self.assertEqual(effects['acquisitions'][0]['commit'],self.row['commit'])
        self.assertNotEqual(effects['acquisitions'][0]['commit'],newer)
        self.assertEqual((self.project/'.mask.lock.json').read_bytes(),original)
        self.assertFalse((cache/'mask-refs.json').exists())

    def test_adoption_stale_and_malformed_pending_files_refuse(self):
        self.register()
        self.declaration['skills'].append(dict(source=TAP,id='beta'))
        candidate=r.resolve_candidate(self.declaration,self.config,self.home,self.lock)
        (self.project/'.mask.json').write_text(c.text_json(self.declaration))
        (self.project/'.mask.lock.json').write_text(c.text_json(candidate))
        before=self.snapshot()
        self.assertEqual(self.call('link','adopt','--project',self.project,'--skill','beta','--target','codex','--expect-source',self.base/'unused',code=4)['error']['code'],'target.adoption_stale')
        self.assertEqual(before,self.snapshot())
        state=c.state(c.read_json(self.home/'state.json'))
        planned=fs.plan(self.config,state,[self.project],home=self.home)
        journal=fs.make_pending(planned,self.home)
        journal['files']={}
        with self.assertRaises(c.MaskError) as error:fs.validate_pending(journal,self.home)
        self.assertEqual(error.exception.code,'recovery.conflict')

    def test_real_branch_movement_refuses_recovery_and_preserves_leaf(self):
        self.register()
        self.git(self.project,'config','user.name','Fixture')
        self.git(self.project,'config','user.email','fixture@example.invalid')
        self.git(self.project,'add','.mask.json','.mask.lock.json')
        self.git(self.project,'commit','-m','before crash')
        self.crash('link')
        leaf=self.project/'.agents/skills/alpha'
        raw=os.readlink(leaf)
        (self.project/'branch-change').write_text('new HEAD')
        self.git(self.project,'add','branch-change')
        self.git(self.project,'commit','-m','moved HEAD')
        before=self.snapshot()
        self.call('recover','--complete',code=8)
        self.assertEqual(before,self.snapshot())
        self.assertEqual(os.readlink(leaf),raw)

    def test_artifact_verification_per_link_is_linear(self):
        self.add_skill('gamma')
        self.publish('third skill')
        self.call('source','fetch',TAP)
        self.declaration['skills']=[dict(source=TAP,id=name) for name in ('alpha','beta','gamma')]
        (self.project/'.mask.json').write_text(c.text_json(self.declaration))
        self.call('lock','--refresh')
        self.register()
        self.call('source','fetch','--locked','--offline')
        state=c.state(c.read_json(self.home/'state.json'))
        planned=fs.plan(self.config,state,[self.project],home=self.home)
        journal=fs.make_pending(planned,self.home)
        with patch.object(store,'verify',wraps=store.verify) as verify:
            fs.restore(journal,self.home,'after')
        self.assertEqual(verify.call_count,9) # 3 unique preflight + 6 relevant activations.

    def test_cache_only_restore_and_late_engine_failure_keep_effects(self):
        self.register(True)
        root,_=store.location(self.home,self.row['payload_digest'],'alpha')
        root.rename(self.base/'retained-artifact')
        ready=self.call('apply')
        self.assertTrue(ready['changed'])
        self.assertTrue(ready['data']['preparation'][0]['effects']['artifacts'][0]['created'])
        root.rename(self.base/'retained-artifact-two')
        parser,leaves=mask.make_parser();args=parser.parse_args(['apply','--project',str(self.project),'--home',str(self.home)])
        output=mask.result('apply')
        def fail(*args):
            output['data']={}
            c.fail('fixture.failed','Failure after data replacement.',4)
        with patch.object(mask,'local_dispatch',side_effect=fail),self.assertRaises(c.MaskError):
            mask.dispatch(args,output,leaves)
        self.assertTrue(output['changed'])
        self.assertEqual(output['transaction'],'not_started') # MASK-0110: retained preparation is not a consumer transaction.
        self.assertTrue(output['data']['preparation'][0]['effects']['artifacts'][0]['created'])
        self.assertEqual(output['data']['retained_preparation']['artifacts'],[output['data']['preparation'][0]['effects']['artifacts'][0]['path']])

    def test_inactive_pinned_branch_requires_recorded_lock_evidence(self):
        self.git(self.project,'config','user.name','Fixture')
        self.git(self.project,'config','user.email','fixture@example.invalid')
        self.git(self.project,'add','.mask.json','.mask.lock.json')
        self.git(self.project,'commit','-m','active pinned branch')
        self.call('integration','approve','--project',self.project,'--inactive-branches')
        self.call('ensure')
        tracked=c.read_json(self.home/'integration.json')['approvals'][str(self.project)]['tracked']
        self.assertIn('lock_digest',tracked)
        self.git(self.project,'checkout','-b','inactive')
        self.git(self.project,'rm','.mask.json','.mask.lock.json')
        self.git(self.project,'commit','-m','intentional inactive branch')
        result=self.call('ensure','--event','post-checkout')
        self.assertEqual(result['data']['readiness'],'inactive_on_branch')
        self.assertFalse((self.project/'.agents/skills/alpha').is_symlink())
        self.git(self.project,'checkout','main')
        self.assertEqual(self.call('ensure','--event','post-checkout')['data']['readiness'],'ready_pinned')

    def test_pending_source_authority_and_live_lock_coherence_are_bound(self):
        self.register()
        state=c.state(c.read_json(self.home/'state.json'))
        planned=fs.plan(self.config,state,[self.project],home=self.home)
        pending=fs.make_pending(planned,self.home)
        bad=copy.deepcopy(pending)
        record=bad['after_state']['projects'][str(self.project)]
        record['last_manifest']['sources'][TAP]['repository']='https://invalid.example/rebound'
        record['last_manifest_digest']=r.selection_digest(record['last_manifest'])
        record['last_lock']['selection_digest']=record['last_manifest_digest']
        for row in record['last_lock']['packages']:
            row['repository']='https://invalid.example/rebound'
        for link in record['links'].values():
            link['resolution']['repository']='https://invalid.example/rebound'
        bad['after_state_text']=c.text_json(bad['after_state'])
        with self.assertRaises(c.MaskError) as error:fs.validate_pending(bad,self.home)
        self.assertEqual(error.exception.code,'recovery.conflict')
        bad=copy.deepcopy(pending)
        value=json.loads(bad['pinned']['workspaces'][0]['lock'])
        value['selection_digest']='sha256:'+'0'*64
        bad['pinned']['workspaces'][0]['lock']=json.dumps(value)
        with self.assertRaises(c.MaskError) as error:fs.validate_pending(bad,self.home)
        self.assertEqual(error.exception.code,'recovery.conflict')

    def test_recovery_dedup_keeps_metadata_claims_and_bad_resolution_typed(self):
        self.register(True)
        state=c.state(c.read_json(self.home/'state.json'))
        planned=fs.plan(self.config,state,[self.project],home=self.home)
        pending=fs.make_pending(planned,self.home)
        after=pending['after_state'];after['generation']+=1
        record=after['projects'][str(self.project)]
        record['last_lock']['packages'][0]['metadata_digest']='sha256:'+'0'*64
        for link in record['links'].values():
            link['resolution']['metadata_digest']='sha256:'+'0'*64
        pending['files']=[dict(root=str(self.project),role='project_lock',before=(self.project/'.mask.lock.json').read_text(),after=c.text_json(record['last_lock']))]
        pending['after_state_text']=c.text_json(after)
        with self.assertRaises(c.MaskError) as error:fs.check_current(pending,self.home)
        self.assertEqual(error.exception.code,'recovery.conflict')
        self.assertEqual(error.exception.details['cause']['code'],'artifact.corrupt')
        bad=copy.deepcopy(state)
        next(iter(bad['projects'][str(self.project)]['links'].values()))['resolution']['source']=[]
        with self.assertRaises(c.MaskError):c.state(bad)

    def test_recovery_cannot_silently_convert_existing_consumer_mode(self):
        self.register(True)
        state=c.state(c.read_json(self.home/'state.json'))
        journal=fs.make_pending(fs.plan(self.config,state,[self.project],home=self.home),self.home)
        record=journal['after_state']['projects'][str(self.project)]
        record.pop('mode');record.pop('last_lock')
        record.update(last_manifest=dict(schema_version=1,skills=['alpha']),last_manifest_digest=c.digest(dict(schema_version=1,skills=['alpha'])),links={})
        journal['after_state']['generation']+=1
        journal['after_state_text']=c.text_json(journal['after_state'])
        with self.assertRaises(c.MaskError) as error:fs.validate_pending(journal,self.home)
        self.assertEqual(error.exception.code,'recovery.conflict')

    def test_saved_journal_cannot_strip_pinned_extension(self):
        self.register()
        state=c.state(c.read_json(self.home/'state.json'))
        journal=fs.make_pending(fs.plan(self.config,state,[self.project],home=self.home),self.home)
        journal.pop('pinned');journal.pop('files')
        (self.home/'pending.json').write_bytes(c.text_json(journal).encode('utf-8'))
        before=self.snapshot()
        self.assertEqual(self.call('recover','--inspect',code=8)['error']['code'],'recovery.conflict')
        self.assertEqual(before,self.snapshot())
        (self.home/'pending.json').unlink()
        abandon=fs.make_pending(fs.plan(self.config,state,[self.project],home=self.home,unregister=[str(self.project)],keep_links=True,operation='project.unregister'),self.home)
        self.assertNotIn('pinned',abandon)
        fs.validate_pending(abandon,self.home)

    def test_saved_journal_selecting_a_legacy_record_is_retired(self):
        # Split from test_saved_journal_cannot_strip_pinned_extension. A journal over mode-less ownership records a retired
        # live-checkout transition: inspection reports it, and neither completion nor rollback replays it.
        self.register()
        legacy,record=self.legacy_record('legacy-selected',['beta'])
        state=c.state(c.read_json(self.home/'state.json'))
        planned=fs.plan(self.config,state,[legacy],home=self.home)
        self.assertEqual(planned['blockers'][0]['code'],'migration.required')
        journal=fs.make_pending(planned,self.home)
        with self.assertRaises(c.MaskError) as error:fs.validate_pending(journal,self.home)
        self.assertEqual((error.exception.code,error.exception.details.get('retired')),('recovery.conflict','legacy_ownership'))
        (self.home/'pending.json').write_bytes(c.text_json(journal).encode('utf-8'))
        before=self.snapshot()
        self.assertEqual(self.call('recover','--inspect')['data']['retired'],'legacy_ownership')
        for mode in ('--complete','--rollback'):
            refused=self.call('recover',mode,code=8)['error']
            self.assertEqual((refused['code'],refused['details'].get('retired')),('recovery.conflict','legacy_ownership'))
        self.assertEqual(before,self.snapshot())
        (self.home/'pending.json').unlink()
        self.call('self','install','--bin-dir',self.base/'bin')
        state=c.read_json(self.home/'state.json')
        self.assertEqual(state['schema_version'],3)
        self.assertEqual(state['projects'][str(legacy)],record)

    def test_retarget_unlink_crash_and_transient_create_failure_recover(self):
        self.register(True)
        leaf=self.project/'.agents/skills/alpha'
        for mode in ('rollback','complete','transient'):
            with self.subTest(mode=mode):
                old=os.readlink(leaf)
                (self.source/'skills/alpha/version').write_text(mode)
                self.publish(mode)
                self.call('source','fetch',TAP)
                candidate=r.resolve_candidate(self.declaration,self.config,self.home,self.lock,refresh=True)
                store.ensure(self.home,self.declaration,candidate,self.config)
                (self.project/'.mask.lock.json').write_text(c.text_json(candidate))
                if mode == 'transient':
                    original=Path.symlink_to
                    failed=False
                    def fail_once(path,*args,**kwargs):
                        nonlocal failed
                        if not failed:
                            failed=True
                            raise OSError('fixture transient link creation failure')
                        return original(path,*args,**kwargs)
                    state=c.state(c.read_json(self.home/'state.json'))
                    planned=fs.plan(self.config,state,[self.project],home=self.home)
                    output=mask.result('apply')
                    with patch.object(Path,'symlink_to',fail_once),self.assertRaises(c.MaskError):
                        fs.execute(planned,self.home,output)
                    self.assertEqual(output['transaction'],'rolled_back')
                    self.assertEqual(os.readlink(leaf),old)
                else:
                    self.crash('link_unlinked')
                    self.assertEqual(c.kind(leaf),'missing')
                    self.call('recover','--'+mode)
                    if mode == 'rollback':self.assertEqual(os.readlink(leaf),old)
                    else:self.assertEqual(fs.normalized_link(leaf,os.readlink(leaf)),store.location(self.home,candidate['packages'][0]['payload_digest'],'alpha')[1])
                self.assertFalse((self.home/'pending.json').exists())
                self.call('apply')
