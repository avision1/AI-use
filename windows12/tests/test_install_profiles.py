"""Installation hardware-profile guards; run only inside the contained check VM.

The orchestration case uses synthetic proof and mocks QEMU/network operations.
It tests selected commands and containment, not an installed operating system.
"""
import argparse
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


class InstallProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.module = runpy.run_path(str(PROJECT / 'scripts/install-test.py'), run_name='install_profile_tests')
        cls.parent = PROJECT / '.work/test-install-profiles'
        cls.parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.parent)
        self.root = Path(self.temporary.name)
        self.iso = self.root / 'preview.iso'
        self.iso.write_bytes(b'parser-only ISO fixture')
        self.output = self.root / 'installation'
        self.args = argparse.Namespace(accelerator='tcg', cpu_profile='max',
                                       installer_directory=None, disk_size='24G',
                                       install_timeout=60, boot_timeout=60, interval=1)
        self.guard = self.module['require_accelerator']
        self.globals = self.guard.__globals__

    def tearDown(self):
        self.temporary.cleanup()

    def device(self, mode=stat.S_IFCHR | 0o660, error=None):
        device = Mock()
        device.lstat.side_effect = error
        device.lstat.return_value = argparse.Namespace(st_mode=mode)
        return device

    def test_fixed_profile_matrix_and_tcg_never_probes_kvm(self):
        device = self.device()
        with patch.dict(self.globals, {'KVM_DEVICE': device}), patch('os.access', return_value=True) as access:
            for cpu in ('max', 'Nehalem'):
                self.args.cpu_profile = cpu
                self.assertEqual(self.guard(self.args), ('tcg', cpu))
            device.lstat.assert_not_called()
            access.assert_not_called()
            self.args.accelerator = 'kvm'
            for cpu in ('max', 'Nehalem', 'host'):
                self.args.cpu_profile = cpu
                self.assertEqual(self.guard(self.args), ('kvm', cpu))
            self.assertEqual(device.lstat.call_count, 3)
            access.assert_called_with(device, os.R_OK | os.W_OK)

    def test_kvm_missing_regular_symlink_or_inaccessible_refused_before_output(self):
        execute = self.module['execute']
        cases = ((self.device(error=FileNotFoundError()), True),
                 (self.device(error=PermissionError()), True),
                 (self.device(stat.S_IFREG | 0o660), True),
                 (self.device(stat.S_IFLNK | 0o777), True),
                 (self.device(), False))
        self.args.accelerator, self.args.cpu_profile = 'kvm', 'host'
        for device, accessible in cases:
            with self.subTest(device=device, accessible=accessible), \
                    patch.dict(self.globals, {'KVM_DEVICE': device, 'environment': Mock(), 'installer_files': Mock()}), \
                    patch('os.access', return_value=accessible), \
                    patch('subprocess.run') as run, patch('subprocess.Popen') as spawn:
                with self.assertRaisesRegex(ValueError, 'KVM requires an existing readable/writable'):
                    execute(self.args, self.iso, self.output)
                self.globals['environment'].assert_not_called()
                self.globals['installer_files'].assert_not_called()
                run.assert_not_called()
                spawn.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_host_under_tcg_and_fragments_refused_before_writable_work(self):
        for accelerator, cpu in (('tcg', 'host'), ('kvm,thread=multi', 'host'),
                                 ('tcg', 'max,+avx'), ('other', 'max')):
            self.args.accelerator, self.args.cpu_profile = accelerator, cpu
            with self.subTest(accelerator=accelerator, cpu=cpu), \
                    patch.dict(self.globals, {'environment': Mock(), 'installer_files': Mock()}), \
                    patch('subprocess.run') as run, patch('subprocess.Popen') as spawn:
                with self.assertRaises(ValueError):
                    self.module['execute'](self.args, self.iso, self.output)
                self.globals['environment'].assert_not_called()
                self.globals['installer_files'].assert_not_called()
                run.assert_not_called()
                spawn.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_cli_invalid_profiles_and_host_tcg_refused_before_paths_or_runner(self):
        main = self.module['main']
        cases = (('--accelerator', 'kvm,thread=multi'), ('--accelerator', 'none'),
                 ('--cpu-profile', 'max,+avx'), ('--cpu-profile', '/dev/kvm'))
        for option, value in cases:
            with self.subTest(option=option, value=value), \
                    patch.dict(main.__globals__, {'contained': Mock(), 'exclusive_runner': Mock(), 'execute': Mock()}), \
                    patch.object(sys, 'argv', ['install-test.py', 'unused.iso', option, value]):
                with self.assertRaises(SystemExit) as stopped:
                    main()
                self.assertEqual(stopped.exception.code, 2)
                for name in ('contained', 'exclusive_runner', 'execute'):
                    main.__globals__[name].assert_not_called()
        with patch.dict(main.__globals__, {'contained': Mock(), 'exclusive_runner': Mock(), 'execute': Mock()}), \
                patch.object(sys, 'argv', ['install-test.py', 'unused.iso', '--cpu-profile', 'host']):
            with self.assertRaisesRegex(ValueError, 'host requires --accelerator kvm'):
                main()
            for name in ('contained', 'exclusive_runner', 'execute'):
                main.__globals__[name].assert_not_called()
        self.assertFalse(self.output.exists())

    def test_mocked_phases_share_hardware_and_keep_verification_iso_free(self):
        token = 'a' * 24
        audit = {'default_target': 'graphical.target', 'display_manager_unit': 'sddm.service',
                 'build_proxy_ca_absent': True, 'build_proxy_entries_absent': True}
        server = Mock(server_port=12345)
        completion = Mock()
        completion.is_set.return_value = True
        profiles = (('tcg', 'max'), ('tcg', 'Nehalem'), ('kvm', 'max'),
                    ('kvm', 'Nehalem'), ('kvm', 'host'))
        for number, (accelerator, cpu) in enumerate(profiles):
            output = self.root / f'installation-{number}'
            disk = output / 'disposable-install.qcow2'
            calls = []

            def phase(name, common, extra, destination, env, timeout, interval):
                calls.append((name, list(common), list(extra)))
                serial = destination / (name + '-serial.log')
                if name == 'installed-boot':
                    serial.write_text('WINDOWS12_INSTALLED_BOOT_OK:' + token +
                                      ' root=/dev/vda1 package=0.1.0~preview4 proof_once=' + token + '\n' +
                                      'WINDOWS12_INSTALLED_CONFIG:' + token + ' ' + json.dumps(audit) + '\n')
                return {'returncode': 0, 'timed_out': False, 'serial': str(serial)}

            def create_disk(command, **unused):
                self.assertEqual(command[1:4], ['create', '-f', 'qcow2'])
                self.assertEqual(command[4], str(disk))
                disk.write_bytes(b'parser-only stopped-disk fixture')

            self.args.accelerator, self.args.cpu_profile = accelerator, cpu
            with self.subTest(accelerator=accelerator, cpu=cpu), \
                    patch.dict(self.globals, {'KVM_DEVICE': self.device(), 'environment': Mock(return_value={}),
                                              'installer_files': Mock(return_value=((self.root / 'vmlinuz', self.root / 'initrd'), '/install')),
                                              'run_vm': phase}), \
                    patch('os.access', return_value=True), patch('subprocess.run', side_effect=create_disk), \
                    patch('subprocess.Popen') as spawn, patch('secrets.token_hex', return_value=token), \
                    patch('threading.Event', return_value=completion), patch('threading.Thread'), \
                    patch('http.server.ThreadingHTTPServer', return_value=server):
                self.assertEqual(self.module['execute'](self.args, self.iso, output), 0)
                spawn.assert_not_called()
                self.assertEqual([call[0] for call in calls], ['install', 'installed-boot'])
                common = calls[0][1]
                self.assertEqual(calls[1][1], common)
                self.assertEqual(common[common.index('-machine') + 1], f'pc,accel={accelerator},smm=off')
                self.assertEqual(common[common.index('-cpu') + 1], cpu)
                self.assertIn('virtio-blk-pci,drive=install-disk,serial=W12' + token[:17], common)
                nodes = [json.loads(common[i + 1]) for i, arg in enumerate(common) if arg == '-blockdev']
                self.assertEqual(nodes, [{'driver': 'file', 'filename': str(disk), 'node-name': 'disk-file'},
                                         {'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}])
                self.assertIn('-kernel', calls[0][2])
                self.assertIn('-initrd', calls[0][2])
                iso_nodes = [json.loads(calls[0][2][i + 1]) for i, arg in enumerate(calls[0][2]) if arg == '-blockdev']
                self.assertTrue(iso_nodes and all(node.get('read-only') is True for node in iso_nodes))
                self.assertEqual(calls[1][2], ['-boot', 'order=c', '-nic', 'none'])
                self.assertFalse(any(str(self.iso) in arg for arg in common))
                self.assertFalse(any(arg in common for arg in ('-kernel', '-initrd', '-netdev', '-fsdev')))
                result = json.loads((output / 'result.json').read_text())
                self.assertEqual((result['accelerator'], result['cpu_profile']), (accelerator, cpu))
                self.assertTrue(result['install_verified'] and result['disk_boot_verified'])
                self.assertFalse(result['gui_verified'])
                self.assertIn('in-target --pass-stdout dpkg-query', (output / 'late-install.sh').read_text())
                self.assertIn('sh -x /tmp/windows12-late.sh >/dev/ttyS0 2>&1', (output / 'preseed.cfg').read_text())


if __name__ == '__main__':
    unittest.main()
