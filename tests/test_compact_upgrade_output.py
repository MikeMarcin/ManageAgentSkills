"""Large upgrade transcripts stay readable without hiding consent or partial effects."""
import os
import unittest

import mask
import mask_present as present


class CompactUpgradeOutput(unittest.TestCase):
    def task(self):
        root = os.path.abspath(os.sep + 'fixture')
        projects = ['AgentSkills', 'AllTheThings', 'BetterPullReview', 'ChessStudyBuddy',
                    'FindInMedia', 'GolfSwingFeedback', 'ManageAgentSkills', 'PlaceOfMind', 'SiftThroughLogs']
        roots = [os.path.join(root, 'personal')]
        roots += [os.path.join(root, 'worktrees', name, 'BetterPullReview') for name in ('15a6', '6264', '6ead', 'd061')]
        roots += [os.path.join(root, 'projects', name) for name in projects]
        roots.append(os.path.join(root, 'other', 'aito'))
        skipped = os.path.join(root, 'tasks', 'GolfSwingFeedback')
        error = dict(code='upgrade.commit_ineligible', message='An attached branch with an existing HEAD is required.')
        roles = [agent + '/rfc-role-' + str(i) for agent in ('claude', 'codex') for i in range(9)]
        changes = [dict(coordinate='agentskills/' + skill, before_commit='a' * 40, after_commit='b' * 40)
                   for skill in ('author-rfc', 'grill-rfc', 'implement-rfc')]
        output = mask.result('upgrade')
        output['data']['consumers'] = [dict(root=path, scope='user' if i == 0 else 'project', status='updated', changes=changes)
                                      for i, path in enumerate(roots)]
        output['data']['consumers'].append(dict(root=skipped, scope='project', status='blocked', error=error, changes=changes))
        output['data']['bundle_updates'] = [dict(root=path, definitions=[dict(coordinate='agentskills/rfc', commit='b' * 40,
                                                   definition_digest='sha256:' + 'd' * 64)], added=[], removed=[], preserved=[], versions=changes)
                                            for path in roots[-5:]]
        output['data']['commits'] = [dict(root=path, scope='user' if i == 0 else 'project',
                                         status='not_applicable' if i == 0 else 'planned', paths=['.mask.lock.json'],
                                         included_existing_changes=['.mask.lock.json'] if 1 <= i <= 4 else [],
                                         message='chore(mask): upgrade skills', commit=None, error=None)
                                    for i, path in enumerate(roots)]
        output['data']['commits'].append(dict(root=skipped, scope='project', status='blocked', error=error, commit=None))
        actions, setup = [], []
        for path in roots:
            actions += [dict(kind='link.replace', path=os.path.join(path, '.agents', 'skills', 'implement-rfc')),
                        dict(kind='lock.write', path=os.path.join(path, '.mask.lock.json'))]
            if os.path.basename(path) == 'AllTheThings':
                continue
            targets = [role for role in roles if role.startswith('codex/')] if os.path.basename(path) == 'FindInMedia' else roles
            actions.append(dict(kind='setup.run', root=path, skill='implement-rfc', coordinate='agentskills/implement-rfc',
                                fingerprint='5c0ee271ca58', interpreter='/python', native_roles=targets,
                                path=os.path.join(root, 'store', 'payload', 'implement-rfc', 'scripts', 'prepare_mask_roles.py')))
            setup.append(dict(root=path, subject='agentskills/implement-rfc:prepare-roles', state='granted'))
        proposal = dict(kind='task', scope=roots, actions=actions)
        output['data'].update(review=proposal, setup=dict(actions=setup))
        return output, proposal

    def test_large_review_groups_shared_work_and_keeps_commit_exceptions(self):
        output, proposal = self.task()
        text = present.task_review(proposal, output)
        detailed = present.task_review(proposal, output, details=True)
        self.assertLessEqual(len(text.splitlines()), 26, text)
        self.assertGreater(len(detailed.splitlines()), len(text.splitlines()) * 2)
        self.assertEqual(text.count('agentskills/rfc -> bbbbbbb'), 1)
        self.assertEqual(text.count('prepare_mask_roles.py'), 1)
        self.assertEqual(text.count('agentskills/author-rfc ->'), 1)
        self.assertIn('14 local commits', text)
        self.assertIn('includes existing changes: .mask.lock.json', text)
        self.assertIn('Git commit blocked:', text)
        self.assertIn('14 projects and personal skills', text)
        for root in proposal['scope']:
            self.assertIn(root, detailed)
        self.assertNotIn('sha256:', text)
        self.assertNotIn('rfc-role-', text)
        self.assertIn('5c0ee271ca58', detailed)
        self.assertIn('sha256:', detailed)
        self.assertIn('claude/rfc-role-0', detailed)

    def test_success_counts_unique_skills_and_summarizes_setup_and_commits(self):
        output, _ = self.task()
        output.update(changed=True, transaction='committed')
        output['data']['consumers'] = output['data']['consumers'][:-1]
        output['data']['commits'] = output['data']['commits'][:-1]
        for row in output['data']['setup']['actions']:
            row['state'] = 'published'
        for row in output['data']['commits'][1:]:
            row.update(status='committed', commit='c' * 40)
        text = present.render(output)
        self.assertIn('Upgraded 3 skills', text)
        self.assertIn('Setup: 14/14 completed.', text)
        self.assertIn('14 local commits created.', text)
        self.assertLessEqual(len(text.splitlines()), 12, text)
        self.assertNotIn('not_applicable', text)
        self.assertNotIn('rfc-role-', text)

    def test_shared_bundle_additions_and_overlap_warnings_are_not_repeated(self):
        output, proposal = self.task()
        for row in output['data']['bundle_updates']:
            row['added'] = ['agentskills/new-skill']
        text = present.task_review(proposal, output)
        self.assertEqual(text.count('+ agentskills/new-skill'), 1)
        self.assertIn('+ agentskills/new-skill (5 locations)', text)
        output['warnings'] = [dict(code='target.scope_shadowing', message='overlap', name='implement-rfc',
                                   agent=agent, same_target=False) for agent in ('claude', 'codex')]
        warning = '\n'.join(present.warnings(output))
        self.assertEqual(len(warning.splitlines()), 1)
        self.assertIn('implement-rfc (claude and codex)', warning)
        self.assertIn('Host precedence is unknown', warning)

    def test_partial_setup_names_the_failed_location_and_unstarted_work(self):
        output, _ = self.task()
        setup = output['data']['setup']['actions']
        for row in setup[:11]:
            row['state'] = 'published'
        setup[11].update(state='stale', detail='consumer inputs changed after consent; nothing ran')
        output.update(ok=False, changed=True, transaction='committed', error=dict(code='plan.stale',
                      message='Setup inputs changed after approval; setup did not run in this location.',
                      details=dict(root=setup[11]['root']), remediation=[dict(message='Preview again and pass --approve-plan.')]))
        output['data']['workflow_readiness_observation'] = 'before_setup'
        for row in output['data']['commits'][1:-1]:
            row['status'] = 'not_attempted'
        text = present.render_error(output)
        self.assertIn('Setup: 11/14 completed; 1 stale; 2 not started.', text)
        self.assertIn('stale: ' + setup[11]['root'], text)
        for row in setup[12:]:
            self.assertIn('not started: ' + row['root'], text)
        self.assertIn('not attempted in 14 projects', text)
        self.assertIn('Rerun your upgrade command', text)
        self.assertIn('applied changes remain saved', text)
        self.assertNotIn('--approve-plan', text)
        self.assertNotIn('not_applicable', text)
        self.assertLessEqual(len(text.splitlines()), 16, text)

    def test_aggregate_commit_errors_are_named_once_and_keep_created_commit(self):
        output, _ = self.task()
        commits = output['data']['commits']
        failed = commits[1]
        failure = dict(code='upgrade.commit_failed', message='Git hook failed.')
        failed.update(status='failed', error=failure, commit='c' * 40)
        for row in commits[2:-1]:
            row.update(status='committed', commit='d' * 40)
        for row in output['data']['setup']['actions']:
            row['state'] = 'published'
        output.update(ok=False, changed=True, transaction='committed', error=dict(code='upgrade.incomplete',
                      message='Some project commits failed; applied upgrades and successful commits were retained.',
                      details=dict(errors=[failure, commits[-1]['error']]), remediation=[]))
        text = present.render_error(output)
        self.assertEqual(text.count('Git hook failed.'), 1)
        self.assertIn('Git commit failed: ' + failed['root'], text)
        self.assertIn('commit ccccccc was created', text)
        self.assertIn('13 local commits created', text)
        self.assertNotIn('errors:', text)


if __name__ == '__main__':
    unittest.main()
