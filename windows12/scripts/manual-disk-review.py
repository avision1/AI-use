#!/usr/bin/env python3
"""Review a stopped live-harness disk through a new ISO-free child.

This accepts only desktop-test.py provenance, never an arbitrary disk. It does
not establish that a manual installation succeeded. Root, login and application
evidence must be reviewed separately; automatic verification flags stay false.
"""
import argparse
import errno
import math
import os
from pathlib import Path
import runpy
import shutil
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = runpy.run_path(str(ROOT / 'scripts/desktop-test.py'), run_name='manual_disk_desktop_helpers')
strict_path, fresh, read_evidence, file_snapshot, write_new = (
    DESKTOP[name] for name in ('strict_path', 'fresh', 'read_evidence', 'file_snapshot', 'write_new'))
FALSE_FLAGS = {'boot_verified': False, 'login_verified': False, 'install_verified': False,
               'workflows_verified': False, 'root_verified': False, 'calamares_verified': False}


def no_prior_listener(prior):
    """PID absence is insufficient across namespaces; inspect retained FIFOs too."""
    controls = [strict_path(prior / ('qmp' + suffix)) for suffix in ('.in', '.out')]
    if any(not path.exists() or not stat.S_ISFIFO(path.lstat().st_mode) for path in controls):
        raise ValueError('Prior QMP controls are missing or ambiguous')
    try:
        writer = os.open(controls[0], os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except OSError as error:
        if error.errno != errno.ENXIO:
            raise
    else:
        os.close(writer)
        raise ValueError('Prior desktop QMP listener is still active')


def tools(video):
    root = strict_path(DESKTOP['TOOLS'])
    paths = [strict_path(root / name) for name in
             ('usr/bin/qemu-system-x86_64', 'usr/bin/qemu-img',
              'usr/share/seabios/bios-256k.bin', 'usr/share/qemu')]
    rom = strict_path(paths[2].parent / DESKTOP['VIDEO_PROFILES'][video][1])
    if any(not path.is_file() for path in paths[:3]) or not paths[3].is_dir() or not rom.is_file():
        raise ValueError('Prepared project-local BIOS/QEMU tools are missing')
    return paths


def manual_source(value):
    """Validate a clean stopped live run; no D-I success record is manufactured."""
    result_path = strict_path(value)
    report, result_provenance = read_evidence(result_path)
    prior = result_path.parent
    run, run_provenance = read_evidence(prior / 'run.json')
    if result_path.name != 'result.json' or report.get('output') != str(prior):
        raise ValueError('Live result must belong to its recorded output directory')
    common = ('output', 'iso', 'iso_sha256', 'mode', 'installed_source', 'disposable_disk',
              'network', 'cpu_profile', 'video', 'firmware_profile', 'timeout_seconds', 'started_unix')
    if any(key not in run or key not in report or run[key] != report[key] for key in common):
        raise ValueError('Prior live result and startup provenance disagree')
    if ('accelerator' in run) != ('accelerator' in report) or run.get('accelerator') != report.get('accelerator'):
        raise ValueError('Prior live accelerator provenance disagrees')
    # Legacy records omitted this field; exact command reconstruction below
    # must still demonstrate TCG. Never infer KVM from a missing field.
    prior_accelerator = report.get('accelerator', 'tcg')
    if (report['mode'] != 'live' or report['installed_source'] is not None
            or report['firmware_profile'] not in ('bios', 'uefi')
            or prior_accelerator not in ('tcg', 'kvm')
            or report['network'] not in ('none', 'user')
            or report['cpu_profile'] not in DESKTOP['CPU_PROFILES']
            or report['video'] not in DESKTOP['VIDEO_PROFILES']):
        raise ValueError('Only the fixed live-harness profiles are eligible')
    if (report.get('outcome') not in ('operator-stopped', 'guest-exited')
            or type(report.get('qemu_returncode')) is not int or report['qemu_returncode'] != 0
            or any(key in report for key in ('error', 'cleanup_error', 'qmp_close_error', 'baseline_error', 'firmware_error'))
            or any(report.get(key) is not False for key in ('boot_verified', 'login_verified', 'install_verified', 'workflows_verified'))):
        raise ValueError('Prior live run did not complete cleanly without certification')
    for key in ('started_unix', 'finished_unix'):
        if type(report.get(key)) not in (int, float) or not math.isfinite(report[key]) or report[key] <= 0:
            raise ValueError('Prior live timestamps are missing or invalid')
    if report['finished_unix'] < report['started_unix']:
        raise ValueError('Prior live finish precedes startup')
    if type(report['timeout_seconds']) is not int or not 1 <= report['timeout_seconds'] <= 7200:
        raise ValueError('Prior live deadline is invalid')
    if type(report['iso']) is not str or type(report['disposable_disk']) is not str:
        raise ValueError('Prior ISO and disposable disk paths must be canonical strings')
    iso, disk = strict_path(report['iso']), strict_path(prior / 'disposable-install.qcow2')
    if report['iso'] != str(iso) or report['disposable_disk'] != str(disk):
        raise ValueError('Only the ISO and new disk recorded by this live output are eligible')
    command, _ = DESKTOP['stopped_run'](run)
    no_prior_listener(prior)
    if command.count('-m') != 1:
        raise ValueError('Prior live memory provenance is ambiguous')
    memory_argument = command[command.index('-m') + 1:command.index('-m') + 2]
    if len(memory_argument) != 1 or not memory_argument[0].isdigit() or not 1024 <= int(memory_argument[0]) <= 8192:
        raise ValueError('Prior live memory is outside the fixed range')
    qemu, _, firmware, datadir = tools(report['video'])
    previous_args = argparse.Namespace(memory=int(memory_argument[0]), cpu_profile=report['cpu_profile'],
                                      video=report['video'], network=report['network'], firmware_profile=report['firmware_profile'],
                                      accelerator=prior_accelerator)
    expected = DESKTOP['desktop_command'](previous_args, iso, qemu, firmware, datadir, prior, disk)
    expected += ['-qmp', 'pipe:' + str(prior / 'qmp')]
    if command != expected:
        raise ValueError('Prior live command includes unexpected devices, paths or options')
    iso_seal = file_snapshot(iso, 'iso')
    if iso_seal['sha256'] != report['iso_sha256']:
        raise ValueError('Prior live ISO no longer matches its recorded hash')
    firmware_source = manual_uefi_source(report, run, prior)
    baseline = file_snapshot(disk, 'qcow2')
    return {**firmware_source,'kind': 'manual-live-disk', 'result': result_provenance, 'run': run_provenance,
            'baseline': baseline, 'iso': str(iso), 'iso_sha256': iso_seal['sha256'],
            'iso_snapshot': iso_seal, 'prior_output': str(prior),
            'prior_outcome': report['outcome'], 'prior_accelerator': prior_accelerator,
            'manual_installation_certified': False}


def manual_uefi_source(report, run, prior):
    if report['firmware_profile'] == 'bios':
        if report.get('firmware') is not None or run.get('firmware') is not None:
            raise ValueError('BIOS run must not contain UEFI firmware')
        return {'firmware_profile': 'bios'}
    record = report.get('firmware')
    if (not isinstance(record, dict) or record != run.get('firmware')
            or record.get('profile') != 'uefi' or record.get('inputs_verified') is not True
            or record.get('secure_boot_requested') is not False or record.get('required_smm') is not False
            or report.get('firmware_inputs_unchanged') is not True or 'vars_source' in record):
        raise ValueError('Prior live UEFI firmware verification is incomplete')
    verification, verification_seal = read_evidence(prior / 'firmware-verification.json')
    if verification != record:
        raise ValueError('Prior firmware verification record disagrees')
    inputs = record.get('inputs')
    paths = DESKTOP['uefi_paths']()
    if not isinstance(inputs, dict) or set(inputs) != set(paths):
        raise ValueError('Prior firmware input set differs from fixed normal OVMF')
    for key, path in paths.items():
        if DESKTOP['binary_evidence'](path, 8 * 1024 ** 2)[1] != inputs[key]:
            raise ValueError('Prior original firmware input changed')
    lock, lock_seal = read_evidence(ROOT / 'build/firmware-tools-lock.json')
    entry = lock.get('ovmf', {})
    if lock_seal != record.get('lock') or not isinstance(entry, dict) or not isinstance(entry.get('Filename'), str):
        raise ValueError('Prior firmware lock changed')
    archive = ROOT / '.work/builder/debs' / Path(entry['Filename']).name
    _, archive_seal = DESKTOP['binary_evidence'](archive, 32 * 1024 ** 2)
    if (record.get('package') != {'version': entry.get('Version'), **archive_seal}
            or archive_seal['sha256'] != entry.get('SHA256')):
        raise ValueError('Prior cached firmware package changed')
    initial = record.get('vars_copy_initial', {})
    variables = prior / 'uefi-vars.fd'
    if (not isinstance(initial, dict) or initial.get('path') != str(variables)
            or initial.get('sha256') != inputs['template']['sha256']
            or initial.get('bytes') != inputs['template']['bytes']):
        raise ValueError('Prior live variable store did not start from authenticated template')
    _, final = DESKTOP['binary_evidence'](variables, 8 * 1024 ** 2)
    if final != report.get('uefi_vars_final') or final['bytes'] != inputs['template']['bytes']:
        raise ValueError('Prior final variable store seal changed or has wrong size')
    return {'firmware_profile': 'uefi', 'firmware': record,
            'firmware_verification': verification_seal, 'uefi_vars_baseline': final}


def review(args):
    if (type(args.timeout) is not int or not 1 <= args.timeout <= 7200
            or type(args.memory) is not int or not 1024 <= args.memory <= 8192
            or args.cpu_profile not in DESKTOP['CPU_PROFILES'] or args.video not in DESKTOP['VIDEO_PROFILES']
            or args.accelerator not in ('tcg', 'kvm')):
        raise ValueError('Unsupported manual-review deadline, memory or diagnostic profile')
    with DESKTOP['exclusive_runner']():
        profiles = argparse.Namespace(cpu_profile=args.cpu_profile, video=args.video,
                                      firmware_profile=getattr(args, 'firmware_profile', 'bios'), accelerator=args.accelerator)
        DESKTOP['diagnostic_profiles'](profiles)
        DESKTOP['require_accelerator'](profiles)
        source = manual_source(args.live_result)
        DESKTOP['require_source_firmware'](profiles, source)
        output = fresh(args.output or ROOT / 'artifacts' / ('manual-disk-review-' + str(time.time_ns())))
        if output.is_relative_to(Path(source['prior_output'])):
            raise ValueError('New review output must not modify the prior live output directory')
        qemu, qimg, firmware, datadir = tools(args.video)
        if shutil.disk_usage(output.parent if output.parent.exists() else ROOT).free < 8 * 1024 ** 3:
            raise ValueError('At least8GiB free is required for a retained manual-review child')
        output.mkdir(parents=True, mode=0o700)
        write_new(output / 'manual-source.json', {**source, **FALSE_FLAGS})
        launch_args = argparse.Namespace(iso=Path(source['iso']), installed_result=None, disk_size=None,
                                         output=output, timeout=args.timeout, memory=args.memory,
                                         cpu_profile=args.cpu_profile, video=args.video,
                                         firmware_profile=profiles.firmware_profile, network='none', accelerator=args.accelerator)
        try:
            for key in ('result', 'run'):
                if read_evidence(source[key]['path'])[1] != source[key]:
                    raise ValueError('Prior manual provenance changed before launch')
            return DESKTOP['launch'](launch_args, Path(source['iso']), qemu, qimg, firmware, datadir, output, source)
        except BaseException as error:
            if not (output / 'result.json').exists():
                write_new(output / 'result.json', {'mode': 'manual-disk-review', 'outcome': 'setup-failed',
                          'error': str(error), 'output': str(output), 'installed_source': source,
                          'finished_unix': time.time(), **FALSE_FLAGS})
            raise
        finally:
            summary = {'mode': 'manual-disk-review', 'source_kind': source['kind'],
                       'baseline_unchanged': False, 'finished_unix': time.time(), **FALSE_FLAGS}
            try:
                DESKTOP['baseline_unchanged'](source)
                summary['baseline_unchanged'] = True
            except (OSError, ValueError) as error:
                summary['baseline_error'] = str(error)
            write_new(output / 'manual-review.json', summary)
            if not summary['baseline_unchanged']:
                raise ValueError('Manual-review baseline changed; no result is certified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-result', type=Path, required=True, help='Clean stopped desktop-test result.json with its new disk and matching firmware profile')
    parser.add_argument('--output', type=Path, help='New project-contained review directory')
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--memory', type=int, default=4096)
    parser.add_argument('--cpu-profile', choices=DESKTOP['CPU_PROFILES'], default='max')
    parser.add_argument('--accelerator', choices=('tcg', 'kvm'), default='tcg', help='KVM requires existing access to /dev/kvm')
    parser.add_argument('--firmware-profile', choices=('bios', 'uefi'), default='bios')
    parser.add_argument('--video', choices=tuple(DESKTOP['VIDEO_PROFILES']), default='standard')
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error('A TTY-backed interactive session is required')
    return review(args)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
