"""Exercise project storage guards using mock accounting and QMP controls."""
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]


class BuildMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.module = runpy.run_path(str(PROJECT / 'scripts/build-monitor.py'), run_name='monitor_tests')
        cls.parent = PROJECT / '.work/test-build-monitor'
        cls.parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=self.parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        state = self.module['RUNS']
        self.run = state['paths'](self.root, 'monitor-001')
        self.run['work'].mkdir(parents=True)
        self.run['output'].mkdir(parents=True)
        state['publish'](self.root, self.run, self.run['output'], 'tcg', 'max')
        self.pin = state['active'](self.root)[1]

    def monitor(self, arguments, replies=()):
        main = self.module['main']
        with patch.dict(main.__globals__, ROOT=self.root), \
             patch.object(sys, 'argv', ['build-monitor.py', *arguments]), \
             patch.object(sys, 'stdin', io.StringIO('status\nstop\n')), \
             patch.object(sys, 'stdout', io.StringIO()) as output, \
             patch.object(self.module['time'], 'monotonic', return_value=100), \
             patch.object(self.module['select'], 'select', return_value=([True], [], [])), \
             patch.object(subprocess, 'run', side_effect=replies) as run:
            main()
        return [json.loads(line) for line in output.getvalue().splitlines()], run.call_args_list

    def test_default_skips_project_accounting(self):
        records, calls = self.monitor([])
        self.assertFalse(calls)
        self.assertTrue(all('project_byte_limit' not in record for record in records))

    def test_exact_boundary_pauses_pinned_build_without_resampling_for_status(self):
        records, calls = self.monitor(['--project-byte-limit', '8192'], [
            subprocess.CompletedProcess([], 0, '8192\t.\n', ''),
            subprocess.CompletedProcess([], 0, '{}'),
        ])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].args[0], ['du', '-s', '-x', '-B1', '--', '.'])
        self.assertEqual(calls[0].kwargs['cwd'], self.root)
        self.assertEqual(calls[0].kwargs['timeout'], 15)
        self.assertEqual(calls[1].args[0][-2:], ['--active-sha', self.pin])
        self.assertIn('pause', calls[1].args[0])
        self.assertEqual([r['project_allocated_bytes'] for r in records if 'project_allocated_bytes' in r], [8192])
        self.assertEqual([r['resource_pause_confirmed'] for r in records if 'resource_pause_confirmed' in r], [True])

    def test_accounting_failure_retains_unconfirmed_pause_when_qmp_unavailable(self):
        records, calls = self.monitor(['--project-byte-limit', '8192'], [
            subprocess.TimeoutExpired('du', 15),
            subprocess.CompletedProcess([], 1, 'No VM is listening on QMP'),
        ])
        self.assertEqual(len(calls), 2)
        self.assertTrue(any('project_accounting_error' in record for record in records))
        self.assertEqual([r['resource_pause_confirmed'] for r in records if 'resource_pause_confirmed' in r], [False])
        marker = json.loads((self.run['base'] / 'paused-state.json').read_text())
        self.assertEqual(marker['paused'], 'unconfirmed')
        self.assertTrue(marker['requires_explicit_reconciliation'])
