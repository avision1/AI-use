"""Sealed installed-desktop provenance checks; no emulator is launched.

Run only inside the contained build VM. All synthetic evidence stays within the
guest project; tiny fixtures are parser inputs, not bootable disk/ISO images.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

PROJECT = Path(__file__).resolve().parents[1]


class InstalledDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.module = runpy.run_path(str(PROJECT / 'scripts/desktop-test.py'), run_name='installed_desktop_tests')
        cls.installer = runpy.run_path(str(PROJECT / 'scripts/install-test.py'), run_name='installed_desktop_producer_tests')
        cls.fixture_parent = PROJECT / '.work/test-installed-desktop'
        cls.fixture_parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.fixture_parent)
        self.root = Path(self.temporary.name)
        self.prior = self.root / 'install-test'
        self.prior.mkdir()
        self.output = self.root / 'installed-desktop'
        self.result_path = self.prior / 'result.json'
        self.disk = self.prior / 'disposable-install.qcow2'
        header = bytearray(104)
        header[:4] = b'QFI\xfb'
        header[4:8] = (3).to_bytes(4, 'big')
        header[24:32] = (24 * 1024 ** 3).to_bytes(8, 'big')
        self.disk.write_bytes(header + b'parser-only synthetic disk')
        self.iso = self.root / 'preview.iso'
        self.iso.write_bytes(b'\0' * 32769 + b'CD001' + b'parser-only synthetic ISO')
        self.token = 'a' * 24
        self.audit = {'default_target': 'graphical.target', 'display_manager_unit': 'sddm.service',
                      'build_proxy_ca_absent': True, 'build_proxy_entries_absent': True,
                      'gui_runtime_verified': False}
        serial = ('WINDOWS12_INSTALLED_BOOT_OK:' + self.token + ' root=/dev/vda1 package=0.1.0-preview4 proof_once=' + self.token + '\n'
                  'WINDOWS12_INSTALLED_CONFIG:' + self.token + ' ' + json.dumps(self.audit) + '\n')
        (self.prior / 'installed-boot-serial.log').write_text(serial)
        self.report = {'output': str(self.prior), 'iso': str(self.iso),
                       'iso_sha256': hashlib.sha256(self.iso.read_bytes()).hexdigest(),
                       'disk': str(self.disk), 'install_verified': True, 'disk_boot_verified': True,
                       'proof_service_one_shot': True, 'proof_stamp_reported': True, 'completion_callback': True,
                       'configuration_audit': self.audit, 'installed_package_version': '0.1.0-preview4',
                       'installed_disk': self.installer['seal_installed_disk'](self.disk),
                       'outcome': 'installed-root-boot-proof-passed'}
        disk_nodes = [{'driver': 'file', 'filename': str(self.disk), 'node-name': 'disk-file'},
                      {'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}]
        iso_nodes = [{'driver': 'file', 'filename': str(self.iso), 'read-only': True, 'node-name': 'iso-file'},
                     {'driver': 'raw', 'file': 'iso-file', 'read-only': True, 'node-name': 'live-iso'}]
        self.records = {}
        for phase, key in (('install', 'install_run'), ('installed-boot', 'boot_run')):
            self.report[key] = {'returncode': 0, 'timed_out': False, 'serial': str(self.prior / (phase + '-serial.log'))}
            command = [str(PROJECT / '.work/builder/tools/usr/bin/qemu-system-x86_64')]
            for node in disk_nodes + (iso_nodes if phase == 'install' else []):
                command += ['-blockdev', json.dumps(node)]
            command += ['-device', 'virtio-blk-pci,drive=install-disk,serial=W12' + self.token[:17]]
            command += ['-kernel', str(self.prior / 'vmlinuz'), '-initrd', str(self.prior / 'initrd')] if phase == 'install' else ['-boot', 'order=c', '-nic', 'none']
            self.records[phase] = {'pid': 1234567, 'command': command}
        self.save()
        self.kill_patch = patch('os.kill', side_effect=ProcessLookupError)
        self.kill_mock = self.kill_patch.start()
        self.args = argparse.Namespace(iso=None, installed_result=self.result_path, output=self.output,
                                       disk_size=None, memory=4096, network='none', timeout=1800,
                                       cpu_profile='max', video='standard')

    def tearDown(self):
        self.kill_patch.stop()
        self.temporary.cleanup()

    def save(self):
        self.result_path.write_text(json.dumps(self.report))
        for phase, record in self.records.items():
            (self.prior / (phase + '-run.json')).write_text(json.dumps(record))

    def source(self):
        return self.module['installed_source'](self.result_path)

    def assert_refused_before_output(self):
        with patch('subprocess.Popen') as spawn, patch('subprocess.run') as execute:
            with self.assertRaises((ValueError, OSError)):
                self.module['run'](self.args)
            spawn.assert_not_called()
            execute.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_producer_seal_accepted_and_exact_provenance_retained(self):
        source = self.source()
        for key, value in self.report['installed_disk'].items():
            self.assertEqual(source['baseline'][key], value)
        self.assertEqual(source['result']['sha256'], hashlib.sha256(self.result_path.read_bytes()).hexdigest())
        self.assertEqual(source['proof_token'], self.token)
        self.assertFalse(self.output.exists())
        self.module['baseline_unchanged'](source)

    def test_changed_disk_bytes_refused_even_with_original_mtime(self):
        before = self.disk.stat()
        with self.disk.open('r+b') as stream:
            stream.seek(-1, os.SEEK_END)
            stream.write(b'!')
        os.utime(self.disk, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assert_refused_before_output()

    def test_replaced_baseline_inode_refused_even_with_same_bytes(self):
        before = self.disk.stat()
        replacement = self.prior / 'replacement.qcow2'
        replacement.write_bytes(self.disk.read_bytes())
        os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
        replacement.replace(self.disk)
        self.assert_refused_before_output()

    def test_incomplete_proof_or_old_unsealed_result_refused(self):
        for key in ('install_verified', 'disk_boot_verified', 'proof_service_one_shot', 'proof_stamp_reported', 'completion_callback', 'installed_disk'):
            with self.subTest(key=key):
                saved = self.report.pop(key)
                self.save()
                self.assert_refused_before_output()
                self.report[key] = saved

    def test_ambiguous_json_or_duplicate_serial_proof_refused(self):
        self.result_path.write_text('{"output":"first","output":"second"}')
        self.assert_refused_before_output()
        self.save()
        serial = self.prior / 'installed-boot-serial.log'
        serial.write_text(serial.read_text() * 2)
        self.assert_refused_before_output()

    def test_serial_token_stamp_and_configuration_must_agree(self):
        serial = self.prior / 'installed-boot-serial.log'
        original = serial.read_text()
        for changed in (original.replace('proof_once=' + self.token, 'proof_once=' + 'b' * 24),
                        original.replace('sddm.service', 'other.service'), original.replace('package=0.1.0-preview4', 'package=other')):
            with self.subTest(changed=changed):
                serial.write_text(changed)
                self.assert_refused_before_output()

    def test_changed_iso_or_recorded_disk_path_refused(self):
        self.iso.write_bytes(self.iso.read_bytes() + b'changed')
        self.assert_refused_before_output()
        self.report['iso_sha256'] = hashlib.sha256(self.iso.read_bytes()).hexdigest()
        self.report['disk'] = str(self.prior / 'other.qcow2')
        self.save()
        self.assert_refused_before_output()

    def test_prior_phase_block_graph_and_iso_free_boot_required(self):
        boot = self.records['installed-boot']['command']
        original = list(boot)
        for extra in (['-kernel', 'unexpected'], ['-cdrom', str(self.iso)], ['-drive', 'file=' + str(self.disk)],
                      ['-blockdev', json.dumps({'driver': 'file', 'filename': str(self.iso), 'node-name': 'extra'})]):
            with self.subTest(extra=extra):
                boot[:] = original + extra
                self.save()
                self.assert_refused_before_output()
        boot[:] = original
        install = self.records['install']['command']
        index = install.index('-blockdev') + 1
        node = json.loads(install[index])
        node['filename'] = str(self.prior / 'other.qcow2')
        install[index] = json.dumps(node)
        self.save()
        self.assert_refused_before_output()

    def test_active_prior_pid_and_failed_or_timed_out_phase_refused(self):
        self.kill_mock.side_effect = None
        self.assert_refused_before_output()
        self.kill_mock.side_effect = ProcessLookupError
        for key, value in (('returncode', 1), ('returncode', False), ('timed_out', True)):
            with self.subTest(key=key, value=value):
                previous = self.report['boot_run'][key]
                self.report['boot_run'][key] = value
                self.save()
                self.assert_refused_before_output()
                self.report['boot_run'][key] = previous

    def test_symlinked_result_disk_or_ancestor_and_hardlink_refused(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.prior, target_is_directory=True)
        self.args.installed_result = alias / 'result.json'
        self.assert_refused_before_output()
        self.args.installed_result = self.result_path
        actual = self.prior / 'actual.qcow2'
        self.disk.rename(actual)
        self.disk.symlink_to(actual)
        self.assert_refused_before_output()
        self.disk.unlink()
        actual.rename(self.disk)
        os.link(self.disk, actual)
        self.assert_refused_before_output()

    def test_backing_or_external_data_header_refused_even_if_resealed(self):
        original = self.disk.read_bytes()
        for offset, value in ((8, (104).to_bytes(8, 'big')), (72, (4).to_bytes(8, 'big'))):
            with self.subTest(offset=offset):
                changed = bytearray(original)
                changed[offset:offset + len(value)] = value
                self.disk.write_bytes(changed)
                self.report['installed_disk'] = self.installer['seal_installed_disk'](self.disk)
                self.save()
                self.assert_refused_before_output()

    def test_installed_command_uses_only_new_child_and_readonly_baseline(self):
        source = self.source()
        child = self.output / 'installed-desktop.qcow2'
        command = self.module['desktop_command'](self.args, self.iso, 'qemu', 'bios', 'qemu-data', self.output, child, source)
        self.assertFalse(any(arg in command for arg in ('-kernel', '-initrd', '-append', '-cdrom')))
        self.assertFalse(any(str(self.iso) in arg or 'ide-cd' in arg for arg in command))
        self.assertEqual(command[command.index('-boot') + 1], 'order=c,menu=off')
        nodes = [json.loads(command[index + 1]) for index, arg in enumerate(command) if arg == '-blockdev']
        self.assertEqual([node['node-name'] for node in nodes], ['baseline-file', 'baseline', 'disk-file', 'install-disk'])
        self.assertEqual(nodes[0]['filename'], str(self.disk))
        self.assertIs(nodes[0]['read-only'], True)
        self.assertIs(nodes[1]['read-only'], True)
        self.assertIsNone(nodes[1]['backing'])
        self.assertEqual(nodes[2]['filename'], str(child))
        self.assertEqual(nodes[3]['backing'], 'baseline')

    def test_live_command_preserves_readonly_iso_and_optional_new_disk(self):
        self.args.network = 'user'
        command = self.module['desktop_command'](self.args, self.iso, 'qemu', 'bios', 'data', self.output, self.output / 'disposable-install.qcow2')
        self.assertIn('order=d,menu=off', command)
        self.assertIn('ide-cd,drive=live-iso,id=cdrom', command)
        self.assertIn('user,id=net0', command)
        nodes = [json.loads(command[index + 1]) for index, arg in enumerate(command) if arg == '-blockdev']
        self.assertIs(nodes[0]['read-only'], True)
        self.assertIs(nodes[1]['read-only'], True)
        self.assertNotIn('backing', nodes[-1])

    def test_diagnostic_profiles_preserve_live_and_installed_block_graphs(self):
        source = self.source()
        firmware = self.root / 'firmware/bios-256k.bin'
        for source_mode in (None, source):
            child = self.output / ('installed-desktop.qcow2' if source_mode else 'disposable-install.qcow2')
            default = self.module['desktop_command'](self.args, self.iso, 'qemu', firmware, 'data', self.output, child, source_mode)
            default_nodes = [json.loads(default[index + 1]) for index, arg in enumerate(default) if arg == '-blockdev']
            for cpu in ('max', 'Nehalem'):
                for video, device, rom in (('standard', 'VGA', 'vgabios-stdvga.bin'),
                                            ('virtio', 'virtio-vga', 'vgabios-virtio.bin')):
                    with self.subTest(installed=bool(source_mode), cpu=cpu, video=video):
                        self.args.cpu_profile, self.args.video = cpu, video
                        command = self.module['desktop_command'](self.args, self.iso, 'qemu', firmware, 'data', self.output, child, source_mode)
                        self.assertEqual(command[command.index('-cpu') + 1], cpu)
                        self.assertIn(device + ',romfile=' + str(firmware.parent / rom), command)
                        self.assertEqual(command[command.index('-machine') + 1], 'pc,accel=tcg,smm=off')
                        self.assertEqual([json.loads(command[index + 1]) for index, arg in enumerate(command) if arg == '-blockdev'], default_nodes)
                        self.assertFalse(any('gl=on' in arg or 'virtio-vga-gl' in arg or '/dev/dri' in arg for arg in command))
            self.args.cpu_profile, self.args.video = 'max', 'standard'

    def test_invalid_diagnostic_profiles_refused_before_runtime_work(self):
        main = self.module['main']
        for option, value in (('--cpu-profile', 'host'), ('--cpu-profile', 'max,+avx'),
                              ('--video', 'virtio-vga-gl'), ('--video', 'virtio,gl=on')):
            with self.subTest(option=option, value=value), patch.dict(main.__globals__, {'run': Mock()}) as globals_, patch.object(sys, 'argv', ['desktop-test.py', str(self.iso), option, value]):
                with self.assertRaises(SystemExit) as stopped:
                    main()
                self.assertEqual(stopped.exception.code, 2)
                globals_['run'].assert_not_called()
        self.assertFalse(self.output.exists())

    def test_selected_video_firmware_missing_or_aliased_refused_before_output(self):
        toolroot = self.root / 'tools'
        for leaf in ('usr/bin/qemu-system-x86_64', 'usr/share/seabios/bios-256k.bin',
                     'usr/share/seabios/vgabios-stdvga.bin'):
            target = toolroot / leaf
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'parser-only tool fixture')
        (toolroot / 'usr/share/qemu').mkdir()
        self.args.installed_result, self.args.iso = None, self.iso
        self.args.video = 'virtio'
        execute = self.module['run']
        with patch.dict(execute.__globals__, {'TOOLS': toolroot}), patch('subprocess.Popen') as spawn, patch('subprocess.run') as run_process:
            with self.assertRaisesRegex(ValueError, 'tools are missing'):
                execute(self.args)
            selected = toolroot / 'usr/share/seabios/vgabios-virtio.bin'
            selected.symlink_to(toolroot / 'usr/share/seabios/vgabios-stdvga.bin')
            with self.assertRaisesRegex(ValueError, 'Symlinked runtime paths'):
                execute(self.args)
            spawn.assert_not_called()
            run_process.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_mocked_launch_creates_child_and_records_false_guest_verification(self):
        source = self.source()
        self.args.cpu_profile, self.args.video = 'Nehalem', 'virtio'
        self.output.mkdir()
        child = self.output / 'installed-desktop.qcow2'
        launch = self.module['launch']
        process = Mock(pid=1234568)
        process.poll.return_value = 0
        session = Mock()
        session.loop.return_value = 'operator-stopped'

        def fake_create(command, **kwargs):
            self.assertEqual(command, ['qemu-img', 'create', '-f', 'qcow2', '-F', 'qcow2', '-b', str(self.disk), str(child)])
            self.assertEqual(kwargs['cwd'], self.output)
            self.assertEqual(kwargs['env']['HOME'], str(self.output / 'home'))
            self.assertTrue(kwargs['check'])
            child.write_bytes(b'no emulator or real image created')

        with patch('subprocess.run', side_effect=fake_create) as create, patch('subprocess.Popen', return_value=process) as spawn, patch.dict(launch.__globals__, {
                'BoundedQMP': lambda prefix, events, deadline: Mock(prefix=prefix, deadline=deadline),
                'DesktopSession': Mock(return_value=session), 'stop_owned': Mock()}):
            self.assertEqual(launch(self.args, self.iso, 'qemu', 'qemu-img', 'bios', 'data', self.output, source), 0)
            create.assert_called_once()
            spawn.assert_called_once()
        startup = json.loads((self.output / 'run.json').read_text())
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(startup['disposable_disk'], str(child))
        self.assertEqual(startup['installed_source'], source)
        self.assertEqual(startup['command'], spawn.call_args.args[0])
        self.assertEqual(startup['cpu_profile'], 'Nehalem')
        self.assertEqual(startup['video'], 'virtio')
        self.assertEqual(startup['command'][startup['command'].index('-cpu') + 1], 'Nehalem')
        self.assertIn('virtio-vga,romfile=vgabios-virtio.bin', startup['command'])
        self.assertFalse(any(str(self.iso) in arg for arg in startup['command']))
        self.assertEqual(result['mode'], 'installed')
        self.assertIs(result['baseline_unchanged'], True)
        for key in ('boot_verified', 'login_verified', 'install_verified', 'workflows_verified'):
            self.assertIs(startup[key], False)
            self.assertIs(result[key], False)
        self.module['baseline_unchanged'](source)

    def test_post_session_baseline_change_is_detected(self):
        source = self.source()
        self.disk.write_bytes(self.disk.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'baseline changed'):
            self.module['baseline_unchanged'](source)

    def test_shared_active_runner_refused_before_source_read_or_child_write(self):
        work = self.root / '.work/builder'
        work.mkdir(parents=True)
        main = self.module['main']
        guard = self.module['exclusive_runner']
        with (work / 'runner.lock').open('w') as owner:
            fcntl.flock(owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.dict(guard.__wrapped__.__globals__, {'ROOT': self.root}), patch.dict(main.__globals__, {'run': Mock()}) as globals_, patch.object(sys, 'argv', ['desktop-test.py', '--installed-result', str(self.result_path), '--output', str(self.output)]), patch.object(sys.stdin, 'isatty', return_value=True):
                with self.assertRaisesRegex(ValueError, 'holds runner.lock'):
                    main()
                globals_['run'].assert_not_called()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
