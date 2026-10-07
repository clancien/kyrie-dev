"""Behavioral checks for focused fixes without a full-review baseline."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / 'apply_protocol.py'
spec = importlib.util.spec_from_file_location('apply_protocol', SCRIPT)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ApplyProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = self.root / 'SPEC.md'
        self.companion = self.root / 'acceptance.md'
        self.review = self.root / 'SPEC.review.md'
        self.doc.write_text('CAP-1: behavior\n')
        self.companion.write_text('Acceptance criteria\n')
        self.review.write_text('| R1 | major | missing rejection |\n')
        self.source = self.root / 'snapshot.json'
        self.result = self.root / 'result.json'
        self.findings = self.root / 'findings.json'
        self.capture()

    def capture(self):
        p.write(self.source, p.shared.snapshot(self.doc, [self.companion]))

    def start(self, findings=None, max_rounds=3):
        if findings is None:
            findings = [self.finding('CAP-1:rejection', 'major')]
        p.write(self.findings, findings)
        return p.init(self.doc, self.review, self.source, self.findings, max_rounds)['run']

    def finding(self, key, severity):
        return {'key': key, 'severity': severity, 'finding': 'Behavior undefined',
                'evidence': 'CAP-1 lacks rejection branch', 'source_ids': ['R1']}

    def disposition(self, state='resolved'):
        return {'state': state, 'reason': 'Verified against intent', 'evidence': 'CAP-1 rejection outcome'}

    def record(self, run, coverage='focused', findings=None, checked=None, scope=None, **kwargs):
        self.capture()
        result = {'status': 'complete', 'coverage': coverage,
                  'scope': scope if scope is not None else [str(self.doc), str(self.companion)],
                  'findings': findings or [], 'checked_defects': checked or {},
                  'pending_decisions': [], 'failures': []}
        result.update(kwargs)
        p.write(self.result, result)
        return p.record(run, self.result, self.source)

    def test_begin_uses_existing_markdown_without_full_baseline(self):
        run = self.start()
        state = p.begin(run)
        self.assertEqual(state['rounds_used'], 1)
        self.assertEqual(state['reports'], [])
        self.assertEqual(self.review.read_text(), '| R1 | major | missing rejection |\n')

    def test_focused_clean_never_ready_then_global_ready(self):
        run = self.start()
        p.begin(run)
        self.doc.write_text('CAP-1: rejection outcome defined\n')
        focused = self.record(run, checked={'D1': self.disposition()})
        self.assertEqual(focused['status'], 'active')
        final = self.record(run, 'global', checked={'D1': self.disposition()})
        self.assertEqual(final['status'], 'ready')
        self.assertEqual(p.verify(run)['status'], 'ready')
        self.assertEqual(final['rounds_used'], 1)

    def test_minor_does_not_block_zero_round_global(self):
        run = self.start([self.finding('style', 'minor')])
        final = self.record(run, 'global', checked={'D1': self.disposition('deferred')})
        self.assertEqual(final['status'], 'ready')
        self.assertEqual(final['rounds_used'], 0)
        self.assertEqual(p.read(final['reports'][-1])['verdict'], 'LISTO CON OBSERVACIONES')

    def test_global_requires_full_inventory_and_prior_defects(self):
        run = self.start()
        with self.assertRaisesRegex(ValueError, 'entire current inventory'):
            self.record(run, 'global', checked={'D1': self.disposition()}, scope=[str(self.doc)])
        with self.assertRaisesRegex(ValueError, 'all prior defects'):
            self.record(run, 'global')

    def test_omitted_previous_major_remains_open(self):
        run = self.start()
        p.begin(run)
        state = self.record(run)
        self.assertEqual(state['defects'][0]['state'], 'open')
        final = self.record(run, 'global', checked={'D1': self.disposition('open')})
        self.assertEqual(final['status'], 'active')
        self.assertEqual(p.read(final['reports'][-1])['verdict'], 'NO LISTO')

    def test_major_cannot_be_deferred_or_hidden_by_resolution(self):
        run = self.start()
        p.begin(run)
        with self.assertRaisesRegex(ValueError, 'Only minor'):
            self.record(run, checked={'D1': self.disposition('deferred')})
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            self.record(run, findings=[self.finding('CAP-1:rejection', 'major')], checked={'D1': self.disposition()})

    def test_final_new_major_returns_to_correction(self):
        run = self.start([])
        final = self.record(run, 'global', findings=[self.finding('new-defect', 'major')])
        self.assertEqual(final['status'], 'active')
        self.assertEqual(final['rounds_used'], 0)
        p.begin(run)
        self.assertEqual(p.load_run(run)['rounds_used'], 1)

    def test_budget_counts_retries_and_global_still_allowed(self):
        run = self.start(max_rounds=2)
        p.begin(run)
        p.begin(run)
        state = self.record(run)
        self.assertEqual(state['status'], 'budget_exhausted')
        with self.assertRaises(ValueError):
            p.begin(run)
        self.assertEqual(p.load_run(run)['rounds_used'], 2)

    def test_last_round_resolution_can_close_globally(self):
        run = self.start(max_rounds=1)
        p.begin(run)
        self.record(run, checked={'D1': self.disposition()})
        final = self.record(run, 'global', checked={'D1': self.disposition()})
        self.assertEqual(final['status'], 'ready')

    def test_technical_failure_is_incomplete_not_negative_content_verdict(self):
        run = self.start([])
        state = self.record(run, 'global', status='incomplete', failures=['Unreadable companion'])
        self.assertEqual(state['status'], 'incomplete_review')
        self.assertIsNone(p.read(state['reports'][-1])['verdict'])

    def test_stale_ready_requires_external_refresh_and_global_recheck(self):
        run = self.start([])
        self.record(run, 'global')
        self.companion.write_text('Changed acceptance\n')
        with self.assertRaisesRegex(ValueError, 'Stale snapshot'):
            p.verify(run)
        self.capture()
        refreshed = p.refresh(run, self.source, 'User changed acceptance')
        self.assertEqual(refreshed['status'], 'active')
        self.assertEqual(refreshed['rounds_used'], 0)
        self.assertEqual(self.record(run, 'global')['status'], 'ready')

    def test_own_unbudgeted_change_cannot_be_recorded(self):
        run = self.start([])
        self.doc.write_text('Own uncounted correction\n')
        with self.assertRaisesRegex(ValueError, 'consumed attempt'):
            self.record(run, 'global')

    def test_indispensable_decision_requires_major_blocker(self):
        run = self.start()
        state = self.record(run, 'global', checked={'D1': self.disposition('open')}, pending_decisions=['Which rejection status?'])
        self.assertEqual(state['status'], 'needs_user')
        minor_run = self.start([self.finding('style', 'minor')])
        with self.assertRaisesRegex(ValueError, 'major/blocker'):
            self.record(minor_run, 'global', checked={'D1': self.disposition('deferred')}, pending_decisions=['Preferred phrasing?'])

    def test_resolved_major_reopens_when_substantiated_again(self):
        run = self.start()
        p.begin(run)
        self.record(run, checked={'D1': self.disposition()})
        final = self.record(run, 'global', findings=[self.finding('CAP-1:rejection', 'major')], checked={'D1': self.disposition('open')})
        self.assertEqual(final['defects'][0]['state'], 'open')
        self.assertEqual(len(final['defects']), 1)
        self.assertNotEqual(final['status'], 'ready')

    def test_cli_can_close_from_existing_review_without_full_baseline(self):
        p.write(self.findings, [])
        def cli(*args):
            result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return json.loads(result.stdout)
        run = cli('init', self.doc, '--review', self.review, '--snapshot', self.source,
                  '--findings', self.findings)['run']
        p.write(self.result, {'status': 'complete', 'coverage': 'global',
                'scope': [str(self.doc), str(self.companion)], 'findings': [],
                'checked_defects': {}, 'pending_decisions': [], 'failures': []})
        self.assertEqual(cli('record', run, '--result', self.result,
                             '--snapshot', self.source)['status'], 'ready')
        self.assertEqual(cli('verify', run)['rounds_used'], 0)
        self.assertEqual(self.review.read_text(), '| R1 | major | missing rejection |\n')

    def test_old_policy_halts_without_resetting_budget(self):
        run = self.start()
        p.begin(run)
        state = p.read(run)
        state['policy'] = 'full-spec-v1'
        p.write(run, state)
        before = Path(run).read_bytes()
        with self.assertRaisesRegex(ValueError, 'migrate.*consumed budget'):
            p.begin(run)
        self.assertEqual(Path(run).read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
