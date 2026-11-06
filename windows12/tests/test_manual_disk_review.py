"""Manual live-disk continuation guards; run only in the contained check VM.

Synthetic disk/ISO bytes test provenance, not OS installation. The integration
check mocks QEMU and qemu-img while exercising the actual session orchestration.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch

PROJECT = Path(__file__).resolve().parents[1]


class ManualDiskReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.module = runpy.run_path(str(PROJECT / 'scripts/manual-disk-review.py'), run_name='manual_disk_tests')
        cls.desktop = cls.module['DESKTOP']
        cls.parent = PROJECT / '.work/test-manual-disk-review'
        cls.parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.parent)
        self.root = Path(self.temporary.name)
        self.prior = self.root / 'live'
        self.prior.mkdir()
        self.output = self.root / 'review'
        self.result_path = self.prior / 'result.json'
        self.disk = self.prior / 'disposable-install.qcow2'
        header = bytearray(104)
        header[:4] = b'QFI\xfb'
        header[4:8] = (3).to_bytes(4, 'big')
        header[24:32] = (24 * 1024 ** 3).to_bytes(8, 'big')
        self.disk.write_bytes(header + b'parser-only manual disk')
        self.iso = self.root / 'preview.iso'
        self.iso.write_bytes(b'\0' * 32769 + b'CD001' + b'parser-only ISO')
        for suffix in ('.in', '.out'):
            os.mkfifo(self.prior / ('qmp' + suffix))
        self.toolroot = self.root / '.work/builder/tools'
        for leaf in ('usr/bin/qemu-system-x86_64', 'usr/bin/qemu-img', 'usr/share/seabios/bios-256k.bin',
                     'usr/share/seabios/vgabios-stdvga.bin', 'usr/share/seabios/vgabios-virtio.bin'):
            p = self.toolroot / leaf
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'parser-only tool')
        (self.toolroot / 'usr/share/qemu').mkdir(parents=True)
        self.tools_patch = patch.dict(self.desktop, {'TOOLS': self.toolroot})
        self.tools_patch.start()
        # contextmanager's public wrapper lives in contextlib; patch the actual
        # boot-helper generator so its real lock uses this isolated fixture.
        self.lock_globals = self.desktop['exclusive_runner'].__wrapped__.__globals__
        self.lock_patch = patch.dict(self.lock_globals, {'ROOT': self.root})
        self.lock_patch.start()
        self.kill_patch = patch('os.kill', side_effect=ProcessLookupError)
        self.kill_mock = self.kill_patch.start()
        self.space_patch = patch('shutil.disk_usage', return_value=argparse.Namespace(free=16 * 1024 ** 3))
        self.space_patch.start()
        self.args = argparse.Namespace(live_result=self.result_path, output=self.output, timeout=1800,
                                       memory=4096, cpu_profile='max', video='standard', accelerator='tcg')
        previous = argparse.Namespace(memory=4096, cpu_profile='max', video='standard',
                                      firmware_profile='bios', network='none', accelerator='tcg')
        self.run = {'output': str(self.prior), 'iso': str(self.iso),
                    'iso_sha256': hashlib.sha256(self.iso.read_bytes()).hexdigest(),
                    'mode': 'live', 'installed_source': None, 'disposable_disk': str(self.disk),
                    'network': 'none', 'cpu_profile': 'max', 'video': 'standard', 'firmware_profile': 'bios',
                    'accelerator': 'tcg',
                    'firmware': None, 'timeout_seconds': 1800, 'started_unix': 1000.0,
                    'pid': 1234567}
        qemu, _, firmware, datadir = self.module['tools']('standard')
        self.run['command'] = self.desktop['desktop_command'](previous, self.iso, qemu, firmware, datadir, self.prior, self.disk)
        self.run['command'] += ['-qmp', 'pipe:' + str(self.prior / 'qmp')]
        self.report = {key: value for key, value in self.run.items() if key not in ('pid', 'command')}
        self.report.update(outcome='operator-stopped', qemu_returncode=0, finished_unix=1100.0,
                           boot_verified=False, login_verified=False, install_verified=False, workflows_verified=False)
        self.save()

    def tearDown(self):
        self.kill_patch.stop()
        self.space_patch.stop()
        self.lock_patch.stop()
        self.tools_patch.stop()
        self.temporary.cleanup()

    def save(self):
        self.result_path.write_text(json.dumps(self.report))
        (self.prior / 'run.json').write_text(json.dumps(self.run))

    def refuse(self):
        with patch.dict(self.desktop, {'launch': Mock()}) as unused, patch('subprocess.Popen') as spawn:
            with self.assertRaises((ValueError, OSError)):
                self.module['review'](self.args)
            self.desktop['launch'].assert_not_called()
            spawn.assert_not_called()
        self.assertFalse(self.output.exists())

    def uefi_source_fixture(self):
        fw = self.root / 'firmware'
        paths = {}
        for name, relative in self.desktop['UEFI_MEMBERS'].items():
            path = fw / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'T' * 32 if name == 'template' else b'normal-' + name.encode())
            paths[name] = path
        archive = self.root / '.work/builder/debs/ovmf_fixture.deb'
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(b'!<arch>\nfixture')
        lock = self.root / 'build/firmware-tools-lock.json'
        lock.parent.mkdir()
        lock.write_text(json.dumps({'ovmf': {'Version': 'fixture', 'Filename': 'pool/ovmf_fixture.deb',
                                            'SHA256': hashlib.sha256(archive.read_bytes()).hexdigest()}}))
        inputs = {name: self.desktop['binary_evidence'](path, 8 * 1024 ** 2)[1] for name, path in paths.items()}
        variables = self.prior / 'uefi-vars.fd'
        variables.write_bytes(b'T' * 32)
        record = {'profile': 'uefi', 'inputs_verified': True, 'secure_boot_requested': False,
                  'required_smm': False, 'inputs': inputs, 'lock': self.desktop['read_evidence'](lock)[1],
                  'package': {'version': 'fixture', **self.desktop['binary_evidence'](archive, 32 * 1024 ** 2)[1]},
                  'vars_copy_initial': self.desktop['binary_evidence'](variables, 8 * 1024 ** 2)[1]}
        variables.write_bytes(b'BOOT_ENTRY_MARKER'.ljust(32, b'!'))
        (self.prior / 'firmware-verification.json').write_text(json.dumps(record))
        self.run.update(firmware_profile='uefi', firmware=record)
        self.report.update(firmware_profile='uefi', firmware=record, firmware_inputs_unchanged=True,
                           uefi_vars_final=self.desktop['binary_evidence'](variables, 8 * 1024 ** 2)[1])
        previous = argparse.Namespace(memory=4096, cpu_profile='max', video='standard',
                                      firmware_profile='uefi', network='none', accelerator='tcg')
        qemu, _, bios, datadir = self.module['tools']('standard')
        with patch.dict(self.desktop['uefi_paths'].__globals__, {'FIRMWARE_TOOLS': fw}):
            self.run['command'] = self.desktop['desktop_command'](previous, self.iso, qemu, bios, datadir, self.prior, self.disk)
        self.run['command'] += ['-qmp', 'pipe:' + str(self.prior / 'qmp')]
        self.save()
        return fw, variables

    def test_stopped_manual_uefi_requires_exact_final_vars_and_explicit_profile(self):
        fw, variables = self.uefi_source_fixture()
        with patch.dict(self.desktop['uefi_paths'].__globals__, {'FIRMWARE_TOOLS': fw}), patch.dict(self.module['manual_uefi_source'].__globals__, {'ROOT': self.root}):
            source = self.module['manual_source'](self.result_path)
            self.assertEqual(source['uefi_vars_baseline'], self.report['uefi_vars_final'])
            self.assertNotEqual(source['uefi_vars_baseline']['sha256'], source['firmware']['inputs']['template']['sha256'])
            # BIOS default cannot silently adopt an EFI installation.
            self.refuse()
            self.args.firmware_profile = 'uefi'
            self.desktop['require_source_firmware'](self.args, source)
            variables.write_bytes(b'X' * 32)
            self.refuse()

    def test_manual_uefi_refuses_ambiguous_or_incomplete_firmware_seals(self):
        fw, variables = self.uefi_source_fixture()
        self.args.firmware_profile = 'uefi'
        with patch.dict(self.desktop['uefi_paths'].__globals__, {'FIRMWARE_TOOLS': fw}), patch.dict(self.module['manual_uefi_source'].__globals__, {'ROOT': self.root}):
            original = self.report['uefi_vars_final']
            for bad in (None, {}, self.report['firmware']['vars_copy_initial']):
                with self.subTest(bad=bad):
                    self.report['uefi_vars_final'] = bad
                    self.save()
                    self.refuse()
            self.report['uefi_vars_final'] = original
            self.report['firmware_inputs_unchanged'] = False
            self.save()
            self.refuse()
            self.report['firmware_inputs_unchanged'] = True
            self.save()
            variables.unlink()
            variables.symlink_to(fw / self.desktop['UEFI_MEMBERS']['template'])
            self.refuse()

    def test_manual_uefi_refuses_changed_original_firmware(self):
        fw, variables = self.uefi_source_fixture()
        self.args.firmware_profile = 'uefi'
        with patch.dict(self.desktop['uefi_paths'].__globals__, {'FIRMWARE_TOOLS': fw}), patch.dict(self.module['manual_uefi_source'].__globals__, {'ROOT': self.root}):
            code = fw / self.desktop['UEFI_MEMBERS']['code']
            original = code.read_bytes()
            code.write_bytes(b'changed-original-code')
            self.refuse()
            code.write_bytes(original)
            # Even restored bytes have changed identity/timestamps and remain refused.
            self.refuse()

    def test_manual_uefi_refuses_hardlinked_vars(self):
        fw, variables = self.uefi_source_fixture()
        self.args.firmware_profile = 'uefi'
        with patch.dict(self.desktop['uefi_paths'].__globals__, {'FIRMWARE_TOOLS': fw}), patch.dict(self.module['manual_uefi_source'].__globals__, {'ROOT': self.root}):
            os.link(variables, self.prior / 'vars-alias.fd')
            self.refuse()

    def test_manual_provenance_is_separate_from_installed_proof(self):
        source = self.module['manual_source'](self.result_path)
        self.assertEqual(source['kind'], 'manual-live-disk')
        self.assertEqual(source['baseline'], self.desktop['file_snapshot'](self.disk, 'qcow2'))
        self.assertFalse(source['manual_installation_certified'])
        self.assertNotIn('proof_token', source)
        self.assertNotIn('configuration_audit', source)
        self.assertEqual(source['result']['sha256'], hashlib.sha256(self.result_path.read_bytes()).hexdigest())

    def test_legacy_accelerator_is_accepted_only_with_exact_tcg_command(self):
        self.run.pop('accelerator')
        self.report.pop('accelerator')
        self.save()
        self.assertEqual(self.module['manual_source'](self.result_path)['prior_accelerator'], 'tcg')
        i = self.run['command'].index('-machine') + 1
        self.run['command'][i] = self.run['command'][i].replace('accel=tcg', 'accel=kvm')
        self.save()
        self.refuse()

    def test_accelerator_mismatch_or_unavailable_kvm_is_refused(self):
        self.report['accelerator'] = 'kvm'
        self.save()
        self.refuse()
        self.report['accelerator'] = 'tcg'
        self.save()
        self.args.accelerator = 'kvm'
        with patch.dict(self.desktop, {'require_accelerator': Mock(side_effect=ValueError('KVM unavailable'))}):
            self.refuse()

    def test_result_run_identity_and_disk_origin_must_match(self):
        for key, changed in (('iso_sha256', 'f' * 64), ('disposable_disk', str(self.root / 'other.qcow2')),
                             ('output', str(self.root)), ('mode', 'installed'), ('started_unix', 1001.0)):
            with self.subTest(key=key):
                old = self.report[key]
                self.report[key] = changed
                self.save()
                self.refuse()
                self.report[key] = old
        self.save()
        self.run['disposable_disk'] = self.report['disposable_disk'] = str(self.root / 'other.qcow2')
        self.save()
        self.refuse()

    def test_extra_drives_host_shares_and_direct_kernels_are_refused(self):
        original = list(self.run['command'])
        for extra in (['-drive', 'file=/dev/sda'], ['-virtfs', 'local,path=/,mount_tag=host'],
                      ['-fsdev', 'local,id=host,path=/'], ['-kernel', 'unexpected'],
                      ['-blockdev', json.dumps({'driver': 'file', 'filename': str(self.disk), 'node-name': 'extra'})],
                      ['-device', 'usb-host,hostbus=1,hostaddr=1']):
            with self.subTest(extra=extra):
                self.run['command'] = original + extra
                self.save()
                self.refuse()

    def test_failed_unclean_or_certified_live_results_are_refused(self):
        original = dict(self.report)
        for key, value in (('outcome', 'timed-out-not-certified'), ('qemu_returncode', 1),
                           ('qemu_returncode', False), ('cleanup_error', 'unknown stop'),
                           ('qmp_close_error', 'open reader'), ('install_verified', True),
                           ('finished_unix', 999.0)):
            with self.subTest(key=key, value=value):
                self.report = {**original, key: value}
                self.save()
                self.refuse()

    def test_active_or_ambiguous_pid_is_refused_without_signalling(self):
        for side_effect in (None, PermissionError):
            with self.subTest(side_effect=side_effect):
                self.kill_mock.side_effect = side_effect
                self.refuse()
        self.assertTrue(all(call.args == (1234567, 0) for call in self.kill_mock.call_args_list))

    def test_missing_pid_does_not_override_live_qmp_listener(self):
        reader = os.open(self.prior / 'qmp.in', os.O_RDONLY | os.O_NONBLOCK)
        try:
            self.refuse()
        finally:
            os.close(reader)
        (self.prior / 'qmp.out').unlink()
        self.refuse()

    def test_shared_runner_lock_blocks_all_review_work(self):
        lock = self.root / '.work/builder/runner.lock'
        with lock.open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.refuse()

    def test_uefi_and_nonfixed_profiles_are_refused(self):
        self.run['firmware_profile'] = self.report['firmware_profile'] = 'uefi'
        self.save()
        self.refuse()
        self.run['firmware_profile'] = self.report['firmware_profile'] = 'bios'
        self.save()
        self.args.cpu_profile = 'host'
        self.refuse()

    def test_changed_iso_and_indirect_or_aliased_disk_are_refused(self):
        iso = self.iso.read_bytes()
        self.iso.write_bytes(iso + b'changed')
        self.refuse()
        self.iso.write_bytes(iso)
        original = self.disk.read_bytes()
        changed = bytearray(original)
        changed[8:16] = (104).to_bytes(8, 'big')
        self.disk.write_bytes(changed)
        self.refuse()
        self.disk.write_bytes(original)
        alias = self.prior / 'alias.qcow2'
        os.link(self.disk, alias)
        self.refuse()
        alias.unlink()
        self.disk.rename(alias)
        self.disk.symlink_to(alias)
        self.refuse()

    def test_actual_session_orchestration_uses_child_and_preserves_false_flags(self):
        baseline = self.disk.read_bytes()
        process = Mock()
        process.pid = 7654321
        process.poll.return_value = None
        qmp = Mock(prefix=self.output / 'qmp')
        create_commands = []
        def create(command, **kwargs):
            create_commands.append(command)
            self.assertEqual(command[-2], str(self.disk))
            Path(command[-1]).write_bytes(b'parser-only child')
            return Mock(returncode=0)
        def stop(unused_process, unused_qmp):
            process.poll.return_value = 0
        def start(command, **kwargs):
            with (self.root / '.work/builder/runner.lock').open('r+') as lock:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return process
        globals_ = self.desktop['launch'].__globals__
        session = Mock()
        session.loop.return_value = 'operator-stopped'
        with patch.dict(globals_, {'BoundedQMP': Mock(return_value=qmp),
                                  'DesktopSession': Mock(return_value=session), 'stop_owned': stop}), \
             patch('subprocess.run', side_effect=create), patch('subprocess.Popen', side_effect=start):
            self.assertEqual(self.module['review'](self.args), 0)
        self.assertEqual(create_commands[0][-5:-2], ['-F', 'qcow2', '-b'])
        self.assertEqual(self.disk.read_bytes(), baseline)
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(result['mode'], 'manual-disk-review')
        self.assertTrue(result['baseline_unchanged'])
        for key in ('boot_verified', 'login_verified', 'install_verified', 'workflows_verified'):
            self.assertIs(result[key], False)
        summary = json.loads((self.output / 'manual-review.json').read_text())
        self.assertTrue(summary['baseline_unchanged'])
        for key in self.module['FALSE_FLAGS']:
            self.assertIs(summary[key], False)
        run = json.loads((self.output / 'run.json').read_text())
        self.assertNotIn(str(self.iso), run['command'])
        self.assertFalse(any(arg in run['command'] for arg in ('-kernel', '-initrd', '-append', '-drive', '-netdev')))
        nodes = [json.loads(run['command'][i + 1]) for i, arg in enumerate(run['command']) if arg == '-blockdev']
        self.assertEqual([node['node-name'] for node in nodes], ['baseline-file', 'baseline', 'disk-file', 'install-disk'])
        self.assertIs(nodes[0]['read-only'], True)
        self.assertIs(nodes[1]['read-only'], True)
        self.assertIsNone(nodes[1]['backing'])
        self.assertEqual(nodes[-1]['backing'], 'baseline')
        self.assertEqual(run['installed_source']['kind'], 'manual-live-disk')

    def test_postseal_baseline_mutation_is_retained_as_failure(self):
        def changed(*args):
            self.disk.write_bytes(self.disk.read_bytes() + b'mutation')
            return 0
        with patch.dict(self.desktop, {'launch': changed}):
            with self.assertRaisesRegex(ValueError, 'baseline changed'):
                self.module['review'](self.args)
        summary = json.loads((self.output / 'manual-review.json').read_text())
        self.assertFalse(summary['baseline_unchanged'])
        self.assertIn('baseline_error', summary)


if __name__ == '__main__':
    unittest.main()
