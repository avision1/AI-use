"""Sealed installed-desktop provenance checks; no emulator is launched.

Run only inside the contained build VM. All synthetic evidence stays within the
guest project; tiny fixtures are parser inputs, not bootable disk/ISO images.
"""
import argparse
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tarfile
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
                                       cpu_profile='max', video='standard', firmware_profile='bios', accelerator='tcg')

    def tearDown(self):
        self.kill_patch.stop()
        self.temporary.cleanup()

    def save(self):
        self.result_path.write_text(json.dumps(self.report))
        for phase, record in self.records.items():
            (self.prior / (phase + '-run.json')).write_text(json.dumps(record))

    def source(self):
        return self.module['installed_source'](self.result_path)

    def uefi_fixture(self, features=None):
        firmware = self.root / '.work/builder/firmware-tools'
        descriptor = {'interface-types': ['uefi'], 'mapping': {'device': 'flash',
                      'executable': {'filename': '/usr/share/OVMF/OVMF_CODE_4M.fd', 'format': 'raw'},
                      'nvram-template': {'filename': '/usr/share/OVMF/OVMF_VARS_4M.fd', 'format': 'raw'}},
                      'features': features or [], 'targets': [{'architecture': 'x86_64', 'machines': ['pc-q35-*']}]}
        contents = {'code': b'parser-only normal firmware', 'template': b'parser-only empty varstore',
                    'descriptor': json.dumps(descriptor).encode()}
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode='w') as archive:
            for name, relative in self.module['UEFI_MEMBERS'].items():
                path = firmware / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents[name])
                member = tarfile.TarInfo('./' + relative)
                member.size = len(contents[name])
                archive.addfile(member, io.BytesIO(contents[name]))
        archive_bytes = b'!<arch>\n' + hashlib.sha256(payload.getvalue()).digest()
        cached = self.root / '.work/builder/debs/ovmf_fixture_all.deb'
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(archive_bytes)
        lock = self.root / 'build/firmware-tools-lock.json'
        lock.parent.mkdir(exist_ok=True)
        lock.write_text(json.dumps({'ovmf': {'Package': 'ovmf', 'Version': 'fixture',
                        'Filename': 'pool/ovmf_fixture_all.deb', 'SHA256': hashlib.sha256(archive_bytes).hexdigest()}}))
        return firmware, contents, archive_bytes, payload.getvalue(), cached

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
        for source_mode in (None, source, {**source, 'kind': 'manual-live-disk'}):
            child = self.output / ('installed-desktop.qcow2' if source_mode else 'disposable-install.qcow2')
            default = self.module['desktop_command'](self.args, self.iso, 'qemu', firmware, 'data', self.output, child, source_mode)
            default_nodes = [json.loads(default[index + 1]) for index, arg in enumerate(default) if arg == '-blockdev']
            for accelerator, cpu in (('tcg', 'max'), ('tcg', 'Nehalem'),
                                     ('kvm', 'max'), ('kvm', 'Nehalem'), ('kvm', 'host')):
                for video, device, rom in (('standard', 'VGA', 'vgabios-stdvga.bin'),
                                            ('virtio', 'virtio-vga', 'vgabios-virtio.bin')):
                    with self.subTest(mode=source_mode and source_mode.get('kind', 'installed'), accelerator=accelerator, cpu=cpu, video=video):
                        self.args.cpu_profile, self.args.video, self.args.accelerator = cpu, video, accelerator
                        command = self.module['desktop_command'](self.args, self.iso, 'qemu', firmware, 'data', self.output, child, source_mode)
                        self.assertEqual(command[command.index('-cpu') + 1], cpu)
                        self.assertIn(device + ',romfile=' + str(firmware.parent / rom), command)
                        self.assertEqual(command[command.index('-machine') + 1], 'pc,accel=' + accelerator + ',smm=off')
                        self.assertEqual([json.loads(command[index + 1]) for index, arg in enumerate(command) if arg == '-blockdev'], default_nodes)
                        self.assertFalse(any('gl=on' in arg or 'virtio-vga-gl' in arg or '/dev/dri' in arg for arg in command))
            self.args.cpu_profile, self.args.video, self.args.accelerator = 'max', 'standard', 'tcg'

    def test_invalid_diagnostic_profiles_refused_before_runtime_work(self):
        main = self.module['main']
        for option, value in (('--cpu-profile', 'host'), ('--cpu-profile', 'max,+avx'),
                              ('--video', 'virtio-vga-gl'), ('--video', 'virtio,gl=on'),
                              ('--firmware-profile', '/external/code.fd'), ('--firmware-profile', 'secureboot'),
                              ('--accelerator', 'kvm:tcg')):
            with self.subTest(option=option, value=value), patch.dict(main.__globals__, {'run': Mock()}) as globals_, patch.object(sys, 'argv', ['desktop-test.py', str(self.iso), option, value]):
                with self.assertRaises(SystemExit) as stopped:
                    main()
                self.assertEqual(stopped.exception.code, 2)
                globals_['run'].assert_not_called()
        self.assertFalse(self.output.exists())

    def test_kvm_unavailable_or_without_rw_access_refused_before_source_or_output(self):
        self.args.accelerator, self.args.cpu_profile = 'kvm', 'host'
        execute = self.module['run']
        for is_device, permitted in ((False, True), (True, False)):
            device = Mock()
            device.is_char_device.return_value = is_device
            with self.subTest(is_device=is_device, permitted=permitted), patch.dict(execute.__globals__, {
                    'KVM_DEVICE': device, 'installed_source': Mock()}) as globals_, patch('os.access', return_value=permitted) as access, patch('subprocess.Popen') as spawn:
                with self.assertRaisesRegex(ValueError, 'KVM requires existing readable/writable'):
                    execute(self.args)
                globals_['installed_source'].assert_not_called()
                spawn.assert_not_called()
                if is_device:
                    access.assert_called_once_with(device, os.R_OK | os.W_OK)
                else:
                    access.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_tcg_host_refused_before_device_check_and_kvm_host_explicitly_allowed(self):
        self.args.cpu_profile = 'host'
        validate = self.module['require_accelerator']
        device = Mock()
        device.is_char_device.return_value = True
        with patch.dict(validate.__globals__, {'KVM_DEVICE': device}), patch('os.access', return_value=True) as access:
            with self.assertRaisesRegex(ValueError, 'requires explicitly selected KVM'):
                validate(self.args)
            device.is_char_device.assert_not_called()
            access.assert_not_called()
            self.args.accelerator = 'kvm'
            validate(self.args)
            device.is_char_device.assert_called_once()
            access.assert_called_once_with(device, os.R_OK | os.W_OK)
        self.assertFalse(self.output.exists())

    def test_installed_uefi_refused_before_source_read_or_output(self):
        self.args.firmware_profile = 'uefi'
        execute = self.module['run']
        with patch.dict(execute.__globals__, {'installed_source': Mock()}) as globals_:
            with self.assertRaisesRegex(ValueError, 'live-ISO-only'):
                execute(self.args)
            globals_['installed_source'].assert_not_called()
        main = self.module['main']
        with patch.dict(main.__globals__, {'run': Mock(), 'exclusive_runner': Mock()}) as globals_, patch.object(sys, 'argv', ['desktop-test.py', '--installed-result', str(self.result_path), '--firmware-profile', 'uefi']):
            with self.assertRaises(SystemExit) as stopped:
                main()
            self.assertEqual(stopped.exception.code, 2)
            globals_['run'].assert_not_called()
            globals_['exclusive_runner'].assert_not_called()
        self.assertFalse(self.output.exists())
        with patch.dict(self.module['launch'].__globals__, {'environment': Mock()}) as globals_:
            with self.assertRaisesRegex(ValueError, 'live-ISO-only'):
                self.module['launch'](self.args, self.iso, 'qemu', 'qimg', 'bios', 'data', self.output,
                                      {'kind': 'manual-live-disk'})
            globals_['environment'].assert_not_called()

    def test_uefi_command_attaches_only_readonly_code_and_output_vars(self):
        self.args.firmware_profile, self.args.cpu_profile, self.args.video = 'uefi', 'Nehalem', 'virtio'
        command = self.module['desktop_command'](self.args, self.iso, 'qemu', 'bios', 'data', self.output)
        self.assertEqual(command[command.index('-machine') + 1], 'q35,accel=tcg,smm=off,pflash0=uefi-code,pflash1=uefi-vars')
        self.assertNotIn('-bios', command)
        nodes = [json.loads(command[index + 1]) for index, arg in enumerate(command) if arg == '-blockdev']
        self.assertEqual([node['node-name'] for node in nodes], ['uefi-code-file', 'uefi-code', 'uefi-vars-file', 'uefi-vars', 'iso-file', 'live-iso'])
        self.assertEqual(nodes[0]['filename'], str(self.module['FIRMWARE_TOOLS'] / self.module['UEFI_MEMBERS']['code']))
        self.assertIs(nodes[0]['read-only'], True)
        self.assertIs(nodes[1]['read-only'], True)
        self.assertEqual(nodes[2]['filename'], str(self.output / 'uefi-vars.fd'))
        self.assertNotIn('read-only', nodes[2])
        self.assertNotIn('read-only', nodes[3])
        self.assertIs(nodes[4]['read-only'], True)
        self.assertIs(nodes[5]['read-only'], True)
        self.assertFalse(any('OVMF_VARS_4M.fd' in arg or '/dev/' in arg or '-gl' in arg for arg in command))
        self.args.accelerator, self.args.cpu_profile = 'kvm', 'host'
        kvm_command = self.module['desktop_command'](self.args, self.iso, 'qemu', 'bios', 'data', self.output)
        self.assertEqual(kvm_command[kvm_command.index('-machine') + 1], 'q35,accel=kvm,smm=off,pflash0=uefi-code,pflash1=uefi-vars')
        self.assertEqual(kvm_command[kvm_command.index('-cpu') + 1], 'host')
        self.assertEqual([json.loads(kvm_command[index + 1]) for index, arg in enumerate(kvm_command) if arg == '-blockdev'], nodes)

    def test_missing_uefi_input_refused_before_output(self):
        tools = self.root / 'tools'
        for relative in ('usr/bin/qemu-system-x86_64', 'usr/share/seabios/bios-256k.bin', 'usr/share/seabios/vgabios-stdvga.bin'):
            path = tools / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'parser-only tool fixture')
        (tools / 'usr/share/qemu').mkdir()
        self.args.installed_result, self.args.iso, self.args.firmware_profile = None, self.iso, 'uefi'
        execute = self.module['run']
        with patch.dict(execute.__globals__, {'TOOLS': tools, 'FIRMWARE_TOOLS': self.root / 'absent-firmware'}), patch('subprocess.Popen') as spawn, patch('subprocess.run') as run_process:
            with self.assertRaisesRegex(ValueError, 'OVMF firmware is missing'):
                execute(self.args)
            spawn.assert_not_called()
            run_process.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_uefi_authentication_copy_and_startup_preserve_inputs_and_false_flags(self):
        firmware, contents, archive_bytes, payload, unused = self.uefi_fixture()
        self.args.installed_result, self.args.iso, self.args.firmware_profile = None, self.iso, 'uefi'
        self.output.mkdir()
        launch = self.module['launch']
        process = Mock(pid=1234568)
        process.poll.return_value = 0
        session = Mock()
        session.loop.return_value = 'operator-stopped'
        with patch.dict(launch.__globals__, {'ROOT': self.root, 'FIRMWARE_TOOLS': firmware,
                'BoundedQMP': lambda prefix, events, deadline: Mock(prefix=prefix, deadline=deadline),
                'DesktopSession': Mock(return_value=session), 'stop_owned': Mock()}), patch('shutil.which', return_value='/usr/bin/dpkg-deb'), patch('subprocess.run', return_value=Mock(stdout=payload)) as unpack, patch('subprocess.Popen', return_value=process) as spawn:
            self.assertEqual(launch(self.args, self.iso, 'qemu', 'qemu-img', 'bios', 'data', self.output), 0)
            self.assertEqual(unpack.call_args.args[0], ['/usr/bin/dpkg-deb', '--fsys-tarfile', '-'])
            self.assertEqual(unpack.call_args.kwargs['input'], archive_bytes)
            self.assertEqual(unpack.call_args.kwargs['cwd'], self.output)
            self.assertNotIn('LD_LIBRARY_PATH', unpack.call_args.kwargs['env'])
            self.assertNotIn('QEMU_MODULE_DIR', unpack.call_args.kwargs['env'])
            spawn.assert_called_once()
        self.assertEqual((self.output / 'uefi-vars.fd').read_bytes(), contents['template'])
        startup = json.loads((self.output / 'run.json').read_text())
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(startup['firmware_profile'], 'uefi')
        self.assertTrue(startup['firmware']['inputs_verified'])
        self.assertEqual(startup['firmware']['vars_copy_initial']['sha256'], hashlib.sha256(contents['template']).hexdigest())
        self.assertEqual(result['uefi_vars_final']['sha256'], hashlib.sha256(contents['template']).hexdigest())
        self.assertIs(result['firmware_inputs_unchanged'], True)
        for name, relative in self.module['UEFI_MEMBERS'].items():
            self.assertEqual((firmware / relative).read_bytes(), contents[name])
        for key in ('boot_verified', 'login_verified', 'install_verified', 'workflows_verified'):
            self.assertIs(startup[key], False)
            self.assertIs(result[key], False)

    def test_manual_uefi_copies_final_nvram_without_changing_originals(self):
        firmware, contents, archive_bytes, payload, cached = self.uefi_fixture()
        prepare = self.module['prepare_uefi']
        prior = self.root / 'manual-uefi-live'
        prior.mkdir()
        with patch.dict(prepare.__globals__, {'ROOT': self.root, 'FIRMWARE_TOOLS': firmware}), patch('shutil.which', return_value='/usr/bin/dpkg-deb'), patch('subprocess.run', return_value=Mock(stdout=payload)):
            record = prepare(prior, {})
            variables = prior / 'uefi-vars.fd'
            # Same-size fixture with a distinct boot-variable marker.
            final = b'B' * len(contents['template'])
            variables.write_bytes(final)
            source = {'kind': 'manual-live-disk', 'firmware_profile': 'uefi', 'firmware': record,
                      'uefi_vars_baseline': self.module['binary_evidence'](variables, 8 * 1024 ** 2)[1]}
            for key in ('run', 'result'):
                path = prior / (key + '.json')
                path.write_text('{}')
                source[key] = self.module['read_evidence'](path)[1]
            source['firmware_verification'] = self.module['read_evidence'](prior / 'firmware-verification.json')[1]
            self.output.mkdir()
            copied = prepare(self.output, {}, source)
            self.assertEqual((self.output / 'uefi-vars.fd').read_bytes(), final)
            self.assertNotEqual(final, contents['template'])
            self.assertEqual(variables.read_bytes(), final)
            self.assertEqual(copied['vars_source'], source['uefi_vars_baseline'])
            self.assertEqual(copied['vars_copy_initial']['sha256'], source['uefi_vars_baseline']['sha256'])
            self.assertNotEqual(copied['vars_copy_initial']['identity'], source['uefi_vars_baseline']['identity'])
            self.args.firmware_profile = 'uefi'
            source['baseline'] = {'path': str(self.disk)}
            command = self.module['desktop_command'](self.args, self.iso, 'qemu', 'bios', 'data', self.output, self.output / 'child.qcow2', source)
            self.assertNotIn('ide-cd,drive=live-iso,id=cdrom', command)
            nodes = [json.loads(command[i + 1]) for i, arg in enumerate(command) if arg == '-blockdev']
            self.assertEqual([node['node-name'] for node in nodes], ['uefi-code-file', 'uefi-code', 'uefi-vars-file', 'uefi-vars', 'baseline-file', 'baseline', 'disk-file', 'install-disk'])
            self.assertTrue(nodes[4]['read-only'])
            self.assertEqual(nodes[-1]['backing'], 'baseline')
            variables.write_bytes(b'X' * len(final))
            with self.assertRaisesRegex(ValueError, 'variable store changed'):
                self.module['manual_firmware_unchanged'](source)
            failed = self.root / 'tampered-final-vars'
            failed.mkdir()
            with self.assertRaisesRegex(ValueError, 'UEFI firmware verification failed'):
                prepare(failed, {}, source)
            self.assertFalse((failed / 'uefi-vars.fd').exists())
        for name, relative in self.module['UEFI_MEMBERS'].items():
            self.assertEqual((firmware / relative).read_bytes(), contents[name])

    def test_tampered_uefi_package_or_prepared_bytes_fail_without_vars_or_vm(self):
        firmware, contents, archive_bytes, payload, cached = self.uefi_fixture()
        prepare = self.module['prepare_uefi']
        for changed in ('archive', 'code', 'template'):
            with self.subTest(changed=changed):
                output = self.root / ('failure-' + changed)
                output.mkdir()
                path = cached if changed == 'archive' else firmware / self.module['UEFI_MEMBERS'][changed]
                original = path.read_bytes()
                path.write_bytes(original + b'tampered')
                with patch.dict(prepare.__globals__, {'ROOT': self.root, 'FIRMWARE_TOOLS': firmware}), patch('shutil.which', return_value='/usr/bin/dpkg-deb'), patch('subprocess.run', return_value=Mock(stdout=payload)), patch('subprocess.Popen') as spawn:
                    with self.assertRaisesRegex(ValueError, 'UEFI firmware verification failed'):
                        prepare(output, {})
                    spawn.assert_not_called()
                path.write_bytes(original)
                self.assertIs(json.loads((output / 'firmware-verification.json').read_text())['inputs_verified'], False)
                self.assertFalse((output / 'uefi-vars.fd').exists())

    def test_authenticated_secure_or_smm_required_descriptor_is_refused(self):
        firmware, unused, archive_bytes, payload, cached = self.uefi_fixture(features=['requires-smm', 'secure-boot'])
        self.output.mkdir()
        prepare = self.module['prepare_uefi']
        with patch.dict(prepare.__globals__, {'ROOT': self.root, 'FIRMWARE_TOOLS': firmware}), patch('shutil.which', return_value='/usr/bin/dpkg-deb'), patch('subprocess.run', return_value=Mock(stdout=payload)):
            with self.assertRaisesRegex(ValueError, 'normal non-Secure-Boot'):
                prepare(self.output, {})
        self.assertFalse((self.output / 'uefi-vars.fd').exists())

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
        self.args.cpu_profile, self.args.video, self.args.accelerator = 'host', 'virtio', 'kvm'
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

        device = Mock()
        device.is_char_device.return_value = True
        with patch('os.access', return_value=True), patch('subprocess.run', side_effect=fake_create) as create, patch('subprocess.Popen', return_value=process) as spawn, patch.dict(launch.__globals__, {
                'KVM_DEVICE': device,
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
        self.assertEqual(startup['cpu_profile'], 'host')
        self.assertEqual(startup['video'], 'virtio')
        self.assertEqual(startup['accelerator'], 'kvm')
        self.assertEqual(result['accelerator'], 'kvm')
        self.assertEqual(startup['command'][startup['command'].index('-cpu') + 1], 'host')
        self.assertEqual(startup['command'][startup['command'].index('-machine') + 1], 'pc,accel=kvm,smm=off')
        self.assertIn('virtio-vga,romfile=vgabios-virtio.bin', startup['command'])
        self.assertFalse(any(str(self.iso) in arg for arg in startup['command']))
        self.assertEqual(result['mode'], 'installed')
        self.assertIs(result['baseline_unchanged'], True)
        for key in ('boot_verified', 'login_verified', 'install_verified', 'workflows_verified'):
            self.assertIs(startup[key], False)
            self.assertIs(result[key], False)
        self.module['baseline_unchanged'](source)

    def test_manual_disk_mode_is_distinct_without_installed_proof_or_success_flags(self):
        source = self.source()
        source['kind'] = 'manual-live-disk'
        self.output.mkdir()
        launch = self.module['launch']
        process = Mock(pid=1234568)
        process.poll.return_value = 0
        session = Mock()
        session.loop.return_value = 'operator-stopped'
        def create_child(command, **kwargs):
            (self.output / 'installed-desktop.qcow2').write_bytes(b'parser-only child')
        with patch('subprocess.run', side_effect=create_child), patch('subprocess.Popen', return_value=process), patch.dict(launch.__globals__, {
                'BoundedQMP': lambda prefix, events, deadline: Mock(prefix=prefix, deadline=deadline),
                'DesktopSession': Mock(return_value=session), 'stop_owned': Mock()}):
            self.assertEqual(launch(self.args, self.iso, 'qemu', 'qemu-img', 'bios', 'data', self.output, source), 0)
        for filename in ('run.json', 'result.json'):
            record = json.loads((self.output / filename).read_text())
            self.assertEqual(record['mode'], 'manual-disk-review')
            self.assertEqual(record['installed_source']['kind'], 'manual-live-disk')
            for key in ('boot_verified', 'login_verified', 'install_verified', 'workflows_verified'):
                self.assertIs(record[key], False)

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
