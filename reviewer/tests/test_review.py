import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from reviewer.core import prepare, evaluate, apply_decision


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.git('config', 'core.hooksPath', '/dev/null')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.root / 'docs').mkdir()
        (self.root / 'docs/help.md').write_text('before')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        (self.root / 'docs/help.md').write_text('after')
        (self.root.parent / 'assignment.md').write_text('Improve help only')
        (self.root.parent / 'evidence.md').write_text('Worker delivery')
        self.policy = {'auto_accept': True, 'task_id': 'T1', 'worker': 'worker',
                       'allowed_paths': ['docs/help.md'], 'required_checks': ['docs'],
                       'checklist': ['scope', 'correctness'], 'category': 'docs'}
        self.packet = self.prepare()
        self.report = {'task_id': 'T1', 'snapshot': self.packet['snapshot'], 'reviewer': 'reviewer',
                       'recommendation': 'accept', 'findings': [],
                       'checklist': {'scope': 'pass', 'correctness': 'pass'}}
        self.verification = {'task_id': 'T1', 'snapshot': self.packet['snapshot'],
                             'verifier': 'coordinator', 'checks': {'docs': 'pass'}}

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def prepare(self):
        return prepare(self.root, 'T1', self.root.parent / 'assignment.md', [self.root.parent / 'evidence.md'])

    def decision(self):
        return evaluate(self.root, self.packet, self.report, self.policy, self.verification)

    def test_happy_acceptance_and_dry_run_does_not_write(self):
        before = sorted(str(p) for p in self.root.rglob('*'))
        self.assertTrue(self.decision()['eligible'])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*')))

    def test_stale_tracked_or_untracked_content_denied(self):
        (self.root / 'docs/help.md').write_text('changed again')
        self.assertFalse(self.decision()['eligible'])
        self.packet = self.prepare()
        (self.root / 'new.txt').write_text('new')
        first = self.prepare()['snapshot']
        (self.root / 'new.txt').write_text('different')
        self.assertNotEqual(first, self.prepare()['snapshot'])

    def test_untracked_text_is_included_in_reviewer_packet(self):
        path = self.root / 'docs/new.md'
        path.write_text('# New document\nReviewed content.\n')
        packet = self.prepare()
        self.assertEqual(
            packet['state']['untracked_files']['docs/new.md'],
            '# New document\nReviewed content.\n',
        )

    def test_binary_changes_require_manual_review(self):
        path = self.root / 'docs/image.bin'
        path.write_bytes(b'\x00\xffbinary')
        self.packet = self.prepare()
        self.report['snapshot'] = self.packet['snapshot']
        self.verification['snapshot'] = self.packet['snapshot']
        self.policy['allowed_paths'].append('docs/image.bin')
        decision = self.decision()
        self.assertFalse(decision['eligible'])
        self.assertIn('Binary changes require coordinator review', decision['reasons'])

    def test_paths_with_control_characters_are_rejected(self):
        with self.assertRaises(ValueError):
            from reviewer.core import relative_path
            relative_path('docs/new\nfile.md')

    def test_missing_evidence_denied(self):
        (self.root.parent / 'evidence.md').unlink()
        self.assertFalse(self.decision()['eligible'])

    def test_out_of_scope_denied(self):
        self.policy['allowed_paths'] = ['other.md']
        self.assertFalse(self.decision()['eligible'])

    def test_self_review_denied(self):
        self.report['reviewer'] = 'worker'
        self.assertFalse(self.decision()['eligible'])

    def test_sensitive_category_and_path_denied(self):
        self.policy['category'] = 'release'
        self.assertFalse(self.decision()['eligible'])
        self.policy['category'] = 'docs'
        (self.root / '.github').mkdir()
        (self.root / '.github/publish.yml').write_text('release')
        self.packet = self.prepare()
        self.report['snapshot'] = self.packet['snapshot']
        self.verification['snapshot'] = self.packet['snapshot']
        self.policy['allowed_paths'].append('.github/publish.yml')
        self.assertFalse(self.decision()['eligible'])

    def test_missing_or_skipped_independent_check_denied(self):
        self.verification['checks'] = {'docs': 'skipped'}
        self.assertFalse(self.decision()['eligible'])
        self.verification['checks'] = {}
        self.assertFalse(self.decision()['eligible'])

    def test_malformed_and_path_escape_denied(self):
        self.report['findings'] = False
        self.assertFalse(self.decision()['eligible'])
        self.policy['allowed_paths'] = ['../escape']
        self.assertFalse(self.decision()['eligible'])

    def test_findings_and_default_policy_denied(self):
        self.report['findings'] = [{'path': 'docs/help.md', 'line': 1, 'severity': 'P2', 'message': 'broken', 'reproduction': 'read'}]
        self.assertFalse(self.decision()['eligible'])
        self.report['findings'] = []
        self.policy['auto_accept'] = False
        self.assertFalse(self.decision()['eligible'])

    def test_explicit_apply_records_acceptance_and_preserves_other_tasks(self):
        coordinator = self.root.parent / 'coordinator'
        coordinator.mkdir()
        subprocess.run(['git', 'init', '-q', str(coordinator)], check=True)
        plan = coordinator / 'plan.json'
        plan.write_text(json.dumps({'tasks': [{'id': 'T1', 'owner': 'worker', 'state': 'dispatched', 'dependencies': []}, {'id': 'T2', 'state': 'planned'}]}))
        receipt = coordinator / 'decision.json'
        apply_decision(self.root, self.packet, self.report, self.policy, self.verification, plan, 'T1', receipt)
        result = json.loads(plan.read_text())
        self.assertEqual(result['tasks'][0]['state'], 'accepted')
        self.assertEqual(result['tasks'][1]['state'], 'planned')
        self.assertEqual(len(result['tasks'][0]['review_history']), 1)
        self.assertEqual(result['tasks'][0]['evidence'], ['decision.json'])
        self.assertTrue(receipt.exists())
        self.assertFalse((coordinator / 'plan.json.review.lock').exists())

    def test_apply_requires_exact_task(self):
        with self.assertRaises(ValueError):
            apply_decision(self.root, self.packet, self.report, self.policy, self.verification, self.root / 'plan.json', 'T2', self.root / 'decision.json')

    def test_tampered_packet_diff_denied(self):
        self.packet['diff'] = 'a reviewer was shown different source'
        self.assertFalse(self.decision()['eligible'])

    def test_symlink_change_requires_manual_review(self):
        (self.root / 'docs/help.md').unlink()
        (self.root / 'docs/help.md').symlink_to(self.root.parent / 'evidence.md')
        self.assertFalse(self.decision()['eligible'])

    def test_sensitive_filename_and_report_check_types_denied(self):
        (self.root / 'auth.py').write_text('security behavior')
        self.packet = self.prepare()
        self.report['snapshot'] = self.packet['snapshot']
        self.verification['snapshot'] = self.packet['snapshot']
        self.policy['allowed_paths'].append('auth.py')
        self.assertFalse(self.decision()['eligible'])

    def test_apply_rejects_plan_inside_reviewed_repository(self):
        with self.assertRaises(ValueError):
            apply_decision(self.root, self.packet, self.report, self.policy, self.verification,
                           self.root / 'plan.json', 'T1', self.root.parent / 'receipt.json')
