"""Fresh builder namespaces and hardware guards; contained guest execution only."""
import io
import json
import os
from pathlib import Path
import runpy
import stat
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

PROJECT = Path(__file__).resolve().parents[1]


class BuilderProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.state = runpy.run_path(str(PROJECT / 'scripts/build-run-state.py'), run_name='builder_profile_state')
        cls.parent = PROJECT / '.work/test-builder-profiles'
        cls.parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.legacy = self.state['paths'](self.root)
        self.legacy['work'].mkdir(parents=True)
        self.legacy['output'].mkdir(parents=True)
        self.legacy['disk'].write_bytes(b'old frozen disk')
        self.legacy['checks'].write_bytes(b'old frozen archive')
        (self.legacy['output'] / 'build.exit').write_text('0\n')

    def candidate(self, slug):
        selected = self.state['require_new'](self.root, slug)
        selected['work'].mkdir(parents=True)
        selected['output'].mkdir(parents=True)
        return selected

    def publish(self, selected, full=True):
        return self.state['publish'](self.root, selected, selected['output'], 'kvm', 'host', full=full)

    def test_default_profile_needs_no_kvm_and_fragments_are_rejected(self):
        with patch.object(Path, 'lstat', side_effect=AssertionError('TCG must not inspect KVM')):
            self.assertEqual(self.state['require_profile']('tcg', 'max', None), ('tcg', 'max'))
        for accelerator, cpu, slug in [('kvm', 'host', None), ('tcg', 'host', 'new'),
                                        ('kvm,thread=multi', 'max', 'new'), ('tcg', 'max,-smp', 'new')]:
            with self.subTest(accelerator=accelerator, cpu=cpu):
                with self.assertRaises(ValueError):
                    self.state['require_profile'](accelerator, cpu, slug)
        self.assertFalse((self.legacy['base'] / 'runs').exists())

    def test_kvm_requires_existing_character_device_and_both_permissions(self):
        for mode, access in [(stat.S_IFREG, True), (stat.S_IFLNK, True), (stat.S_IFCHR, False)]:
            with self.subTest(mode=mode, access=access):
                with patch.object(Path, 'lstat', return_value=Mock(st_mode=mode)), patch.object(os, 'access', return_value=access):
                    with self.assertRaises(ValueError):
                        self.state['require_profile']('kvm', 'host', 'new')
        with patch.object(Path, 'lstat', side_effect=FileNotFoundError):
            with self.assertRaises(ValueError):
                self.state['require_profile']('kvm', 'host', 'new')
        with patch.object(Path, 'lstat', return_value=Mock(st_mode=stat.S_IFCHR)), patch.object(os, 'access', return_value=True) as access:
            for cpu in ('max', 'host'):
                self.assertEqual(self.state['require_profile']('kvm', cpu, 'new'), ('kvm', cpu))
            access.assert_called_with(Path('/dev/kvm'), os.R_OK | os.W_OK)
        self.assertFalse((self.legacy['base'] / 'runs').exists())

    def test_new_slug_has_fixed_paths_and_refuses_existing_or_symlinked_outputs(self):
        for slug in ('', '../old', 'a/b', 'UPPER', 'x;touch', 'x' * 49):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                self.state['require_new'](self.root, slug)
        selected = self.candidate('clock-001')
        self.assertEqual(selected['work'], self.legacy['base'] / 'runs/clock-001')
        self.assertEqual(selected['qmp'], self.legacy['qmp'])
        self.assertEqual(selected['runner_lock'], self.legacy['runner_lock'])
        with self.assertRaises(ValueError):
            self.state['require_new'](self.root, 'clock-001')
        alias = self.root / 'artifacts/vm-build-alias'
        alias.symlink_to(self.legacy['output'], target_is_directory=True)
        with self.assertRaises(ValueError):
            self.state['require_new'](self.root, 'alias')

    def test_active_candidate_does_not_follow_old_success_and_replacement_invalidates_pin(self):
        first = self.candidate('clock-001')
        record = self.publish(first)
        selected, token = self.state['active'](self.root)
        self.assertEqual(selected['output'], first['output'])
        self.assertFalse((selected['output'] / 'build.exit').exists())
        self.assertEqual(selected['nonce'], record['nonce'])
        self.assertFalse((first['output'] / 'run.json').exists())  # descriptor works during preparation
        raw = self.legacy['descriptor'].read_bytes()
        second = self.candidate('clock-002')
        replacement = self.publish(second)
        archive = second['output'] / ('previous-active-build-' + replacement['nonce'] + '.json')
        self.assertEqual(archive.read_bytes(), raw)
        with self.assertRaises(ValueError):
            self.state['unchanged'](self.root, token)
        self.assertEqual(self.legacy['disk'].read_bytes(), b'old frozen disk')
        self.assertEqual(self.legacy['checks'].read_bytes(), b'old frozen archive')
        self.assertEqual((self.legacy['output'] / 'build.exit').read_text(), '0\n')

    def test_descriptor_tampering_and_nonfull_operation_fail_closed(self):
        selected = self.candidate('clock-001')
        valid = self.publish(selected)
        for key, value in [('output', str(self.legacy['output'])), ('nonce', 'bad'),
                           ('accelerator', 'kvm,thread=multi'), ('fresh_run', '../old'),
                           ('kind', 'non-full-operation')]:
            corrupt = dict(valid, **{key: value})
            self.legacy['descriptor'].write_text(json.dumps(corrupt))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.state['active'](self.root)
        self.legacy['descriptor'].write_text('{"schema":1,"schema":1}')
        with self.assertRaises(ValueError):
            self.state['active'](self.root)
        self.legacy['descriptor'].unlink()
        self.publish(selected, full=False)
        with self.assertRaises(ValueError):
            self.state['active'](self.root)

    def test_cli_rejects_invalid_modes_before_writable_output_or_dependencies(self):
        module = runpy.run_path(str(PROJECT / 'scripts/build-vm.py'), run_name='builder_cli_profiles')
        function = module['main']
        namespace = function.__globals__
        for arguments in [('--fresh-run', 'new', '--resume'), ('--fresh-run', 'new', '--probe'),
                          ('--accelerator', 'kvm', '--cpu-profile', 'host'),
                          ('--fresh-run', '../old'), ('--cpu-profile', 'max,-smp')]:
            with self.subTest(arguments=arguments), patch.dict(namespace, ROOT=self.root, BASE_WORK=self.legacy['base']), patch.object(sys, 'argv', ['build-vm.py', *arguments]), patch.object(Path, 'mkdir', side_effect=AssertionError('Invalid CLI wrote output')), patch.object(module['subprocess'], 'run', side_effect=AssertionError('Invalid CLI accessed dependencies')):
                with self.assertRaises(SystemExit) as error:
                    function()
                self.assertEqual(error.exception.code, 2)

    def test_busy_shared_runner_prevents_candidate_creation(self):
        module = runpy.run_path(str(PROJECT / 'scripts/build-vm.py'), run_name='builder_busy_test')
        function = module['main']
        selected = self.state['require_new'](self.root, 'busy-001')
        with patch.dict(function.__globals__, ROOT=self.root, BASE_WORK=self.legacy['base']), patch.object(sys, 'argv', ['build-vm.py', '--fresh-run', 'busy-001']), patch.object(module['fcntl'], 'flock', side_effect=BlockingIOError), patch.object(module['subprocess'], 'run', side_effect=AssertionError('Busy build accessed dependencies')):
            with self.assertRaises(SystemExit):
                function()
        self.assertFalse(selected['work'].exists())
        self.assertFalse(selected['output'].exists())
        self.assertFalse(self.legacy['descriptor'].exists())

    def test_cleanup_selects_only_new_candidate_and_protects_disk_inode(self):
        selected = self.candidate('cleanup-001')
        self.publish(selected)
        selected['disk'].write_bytes(b'new candidate disk')
        stale = selected['work'] / '.build.qcow2.stale'
        stale.write_bytes(b'redundant temporary copy')
        protected = selected['work'] / '.build.qcow2.hardlink'
        os.link(selected['disk'], protected)
        old = self.legacy['work'] / '.build.qcow2.old'
        old.write_bytes(b'old retained temporary copy')
        for path in (stale, protected, old):
            os.utime(path, (1, 1))
        (self.root / 'build').mkdir()
        (self.root / 'build/builder-image.lock.json').write_text(json.dumps({'filename': 'pinned.qcow2'}))
        module = runpy.run_path(str(PROJECT / 'scripts/build-clean-sync.py'), run_name='cleanup_selection_test')
        with patch.dict(module['main'].__globals__, ROOT=self.root), patch.object(sys, 'argv', ['build-clean-sync.py', '--apply']), patch.object(sys, 'stdout', io.StringIO()):
            module['main']()
        self.assertFalse(stale.exists())
        self.assertTrue(protected.exists())
        self.assertTrue(old.exists())
        self.assertEqual(selected['disk'].read_bytes(), b'new candidate disk')

    def test_qmp_pin_is_checked_under_client_lock_before_fifo_io(self):
        first = self.candidate('qmp-001')
        self.publish(first)
        _, old_pin = self.state['active'](self.root)
        self.publish(self.candidate('qmp-002'))
        for suffix in ('.in', '.out'):
            os.mkfifo(str(self.legacy['qmp']) + suffix)
        module = runpy.run_path(str(PROJECT / 'scripts/probe-qmp.py'), run_name='qmp_pin_test')
        opened = []
        locked = []
        original_open = os.open
        def checked_open(path, *args, **kwargs):
            self.assertTrue(locked, 'Descriptor must be checked under client lock')
            opened.append(str(path))
            self.assertNotIn(str(path), [str(self.legacy['qmp']) + '.in', str(self.legacy['qmp']) + '.out'])
            return original_open(path, *args, **kwargs)
        with patch.dict(module['main'].__globals__, ROOT=self.root, WORK=self.legacy['work']), patch.object(sys, 'argv', ['probe-qmp.py', 'pause', '--active-sha', old_pin]), patch.object(module['fcntl'], 'flock', side_effect=lambda *args: locked.append(True)), patch.object(os, 'open', side_effect=checked_open):
            with self.assertRaisesRegex(ValueError, 'descriptor changed'):
                module['main']()
        self.assertTrue(opened)
        self.assertEqual(opened, [str(self.legacy['descriptor'])])

    def test_observers_refuse_corrupt_active_descriptor_before_output(self):
        self.legacy['descriptor'].write_text('{broken')
        for name in ('build-monitor.py', 'build-clean-sync.py', 'validate-after-build.py'):
            module = runpy.run_path(str(PROJECT / 'scripts' / name), run_name='observer_profile_test')
            with self.subTest(script=name), patch.dict(module['main'].__globals__, ROOT=self.root), patch.object(sys, 'argv', [name]), patch.object(module['subprocess'] if 'subprocess' in module else __import__('subprocess'), 'run', side_effect=AssertionError('Observer invoked a helper')), patch.object(Path, 'mkdir', side_effect=AssertionError('Observer wrote output')):
                with self.assertRaises(ValueError):
                    module['main']()
