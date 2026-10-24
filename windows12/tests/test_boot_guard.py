"""VM-run serialization checks. Execute only inside the contained build VM.

No emulator is launched. Test fixtures live beneath this project, including when
running in the guest source copy. These tests do not validate live ISO boot.
"""
import fcntl
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]


class BootGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.module = runpy.run_path(str(PROJECT / 'scripts/boot-test.py'), run_name='boot_guard_tests')
        cls.guard = staticmethod(cls.module['exclusive_runner'])
        cls.main = staticmethod(cls.module['main'])
        cls.fixture_parent = PROJECT / '.work/test-boot-guard'
        cls.fixture_parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.fixture_parent)
        self.root = Path(self.temporary.name)
        self.work = self.root / '.work/builder'
        self.work.mkdir(parents=True)
        self.root_patch = patch.dict(self.guard.__wrapped__.__globals__, {'ROOT': self.root})
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temporary.cleanup()

    def fifo_pair(self):
        for suffix in ('in', 'out'):
            os.mkfifo(self.work / ('qmp.' + suffix), 0o600)

    def test_lock_held_for_whole_capture_call(self):
        def capture(_):
            with (self.work / 'runner.lock').open('r+') as second:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(second.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return 37
        with patch.dict(self.main.__globals__, {'capture': capture}), patch.object(sys, 'argv', ['boot-test.py', 'unused.iso']):
            self.assertEqual(self.main(), 37)
        # Completion releases the guard for the next guest.
        with self.guard():
            pass

    def test_held_runner_lock_rejects_before_any_guest_or_capture(self):
        with (self.work / 'runner.lock').open('w') as owner:
            fcntl.flock(owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.dict(self.main.__globals__, {'capture': unittest.mock.Mock()}) as globals_, patch.object(sys, 'argv', ['boot-test.py', 'unused.iso']), patch('subprocess.Popen') as spawn:
                with self.assertRaisesRegex(ValueError, 'holds runner.lock'):
                    self.main()
                globals_['capture'].assert_not_called()
                spawn.assert_not_called()

    def test_live_legacy_fifo_listener_refused_without_consuming_data(self):
        self.fifo_pair()
        reader = os.open(self.work / 'qmp.in', os.O_RDONLY | os.O_NONBLOCK)
        try:
            with self.assertRaisesRegex(ValueError, 'listener is active'):
                with self.guard():
                    self.fail('Live legacy VM must reject capture')
            self.assertEqual(os.read(reader, 1), b'')
        finally:
            os.close(reader)

    def test_stale_fifo_pair_without_listener_permits_guard(self):
        self.fifo_pair()
        with self.guard():
            self.assertTrue((self.work / 'qmp.in').exists())
        self.assertTrue((self.work / 'qmp.out').exists())

    def test_missing_or_regular_legacy_control_refused(self):
        for suffix in ('in', 'out'):
            with self.subTest(suffix=suffix):
                path = self.work / ('qmp.' + suffix)
                path.touch()
                with self.assertRaisesRegex(ValueError, 'Ambiguous legacy'):
                    with self.guard():
                        self.fail('Incomplete control pair must fail closed')
                path.unlink()
        self.fifo_pair()
        (self.work / 'qmp.out').unlink()
        (self.work / 'qmp.out').touch()
        with self.assertRaisesRegex(ValueError, 'Ambiguous legacy'):
            with self.guard():
                self.fail('Non-FIFO control must fail closed')

    def test_symlink_controls_and_lock_refused(self):
        # Targets are still inside the fixture boundary; no external writes.
        destination = self.root / 'elsewhere'
        destination.touch()
        for name, message in (('qmp.in', 'Ambiguous legacy'), ('runner.lock', 'lock symlink refused')):
            with self.subTest(name=name):
                link = self.work / name
                link.symlink_to(destination)
                with self.assertRaisesRegex(ValueError, message):
                    with self.guard():
                        self.fail('Aliased control must fail closed')
                link.unlink()
                # The qmp.in rejection acquires/creates this regular fixture
                # lock first. Remove it before the runner.lock symlink case.
                if name == 'qmp.in':
                    lock = self.work / 'runner.lock'
                    self.assertFalse(lock.is_symlink())
                    self.assertTrue(lock.is_file())
                    lock.unlink()

    def test_builder_directory_escape_refused_before_lock_write(self):
        self.work.rmdir()
        # Sibling fixture remains inside PROJECT but outside this guard ROOT.
        with tempfile.TemporaryDirectory(dir=self.fixture_parent) as outside:
            self.work.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Path must stay beneath'):
                with self.guard():
                    self.fail('Escaping state path must fail closed')
            self.assertFalse((Path(outside) / 'runner.lock').exists())
            self.work.unlink()

    def test_exception_releases_lock(self):
        with self.assertRaisesRegex(RuntimeError, 'capture failure'):
            with self.guard():
                raise RuntimeError('capture failure')
        with self.guard():
            pass


if __name__ == '__main__':
    unittest.main()
