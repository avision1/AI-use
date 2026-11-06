"""Fixed builder namespaces and a pinned active-run descriptor; no runtime setup."""
from pathlib import Path
import hashlib
import json
import os
import re
import secrets
import stat

KVM_DEVICE = Path('/dev/kvm')


def strict(root, value):
    root = Path(root).resolve()
    path = Path(os.path.abspath(value))
    if path == root or not path.is_relative_to(root) or path.resolve() != path:
        raise ValueError('Builder path escapes project or uses a symlink alias')
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('Builder path symlink refused')
    return path


def paths(root, fresh_run=None):
    root = Path(root).resolve()
    if fresh_run is not None and (not isinstance(fresh_run, str) or
                                  not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,47}', fresh_run)):
        raise ValueError('Fresh run requires a 1-48 character lowercase alphanumeric/hyphen slug')
    base = strict(root, root / '.work/builder')
    work = base if fresh_run is None else strict(root, base / 'runs' / fresh_run)
    output = strict(root, root / 'artifacts' / ('vm-build' if fresh_run is None else 'vm-build-' + fresh_run))
    return {'base': base, 'work': work, 'output': output, 'fresh_run': fresh_run,
            'disk': strict(root, work / 'build.qcow2'), 'checks': strict(root, work / 'checks.tar'),
            'source_lock': strict(root, work / 'build-source.sha256'),
            'descriptor': strict(root, base / 'active-build.json'),
            'runner_lock': strict(root, base / 'runner.lock'), 'qmp': strict(root, base / 'qmp')}


def require_new(root, fresh_run):
    selected = paths(root, fresh_run)
    if fresh_run is None:
        raise ValueError('A fresh-run slug is required for isolated candidate paths')
    if any(selected[key].exists() for key in ('work', 'output')):
        raise ValueError('Fresh run work/output already exists; preserve it and choose a new slug')
    return selected


def require_profile(accelerator, cpu_profile, fresh_run):
    if accelerator not in ('tcg', 'kvm') or cpu_profile not in ('max', 'host'):
        raise ValueError('Unsupported builder accelerator or CPU profile')
    if cpu_profile == 'host' and accelerator != 'kvm':
        raise ValueError('Host CPU requires KVM')
    if (accelerator, cpu_profile) != ('tcg', 'max') and fresh_run is None:
        raise ValueError('Nondefault builder hardware requires --fresh-run')
    if accelerator == 'kvm':
        try:
            info = KVM_DEVICE.lstat()
        except OSError:
            raise ValueError('KVM requires existing readable/writable /dev/kvm') from None
        if not stat.S_ISCHR(info.st_mode) or not os.access(KVM_DEVICE, os.R_OK | os.W_OK):
            raise ValueError('KVM requires existing readable/writable /dev/kvm character device')
    return accelerator, cpu_profile


def read_control(root, value):
    path = strict(root, value)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= 16384:
            raise ValueError('Bounded single-link builder descriptor required')
        raw = source.read(16385)
        after = os.fstat(source.fileno())
    identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if len(raw) > 16384 or identity(before) != identity(after) or identity(before) != identity(path.lstat()):
        raise ValueError('Builder descriptor changed during read')
    return raw


def active(root):
    legacy = paths(root)
    descriptor = legacy['descriptor']
    if not descriptor.exists():
        return legacy, None
    raw = read_control(root, descriptor)
    def unique(pairs):
        record = {}
        for key, value in pairs:
            if key in record:
                raise ValueError('Duplicate builder descriptor key')
            record[key] = value
        return record
    record = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    keys = {'schema', 'kind', 'fresh_run', 'nonce', 'work', 'output', 'disk', 'checks',
            'source_lock', 'qmp', 'accelerator', 'cpu_profile'}
    if not isinstance(record, dict) or set(record) != keys or type(record.get('schema')) is not int or record.get('schema') != 1:
        raise ValueError('Unknown builder descriptor schema')
    if record['kind'] != 'full-build':
        raise ValueError('Active builder operation is not a full image build')
    selected = paths(root, record['fresh_run'])
    if not isinstance(record['nonce'], str) or not re.fullmatch(r'[0-9a-f]{32}', record['nonce']):
        raise ValueError('Invalid builder descriptor nonce')
    if (record['accelerator'], record['cpu_profile']) not in (('tcg', 'max'), ('kvm', 'max'), ('kvm', 'host')):
        raise ValueError('Invalid builder descriptor hardware profile')
    if selected['fresh_run'] is None and (record['accelerator'], record['cpu_profile']) != ('tcg', 'max'):
        raise ValueError('Legacy builder descriptor must retain TCG/max')
    for key in ('work', 'output', 'disk', 'checks', 'source_lock', 'qmp'):
        if record[key] != str(selected[key]):
            raise ValueError('Builder descriptor path disagrees with fixed namespace: ' + key)
    selected['nonce'] = record['nonce']
    return selected, hashlib.sha256(raw).hexdigest()


def unchanged(root, expected):
    selected, actual = active(root)
    if actual != expected:
        raise ValueError('Active builder descriptor changed; reconcile before further observation/control')
    return selected


def publish(root, selected, archive_output, accelerator, cpu_profile, full=True):
    """Called only by the builder while holding the fixed shared runner lock.

    Paths/nonce remain immutable through preparation, VM execution and export.
    Source and exact command provenance are written separately in the run output.
    """
    target = paths(root)['descriptor']
    previous = read_control(root, target) if target.exists() else None
    nonce = secrets.token_hex(16)
    record = {'schema': 1, 'kind': 'full-build' if full else 'non-full-operation',
              'fresh_run': selected['fresh_run'], 'nonce': nonce,
              'accelerator': accelerator, 'cpu_profile': cpu_profile}
    record.update({key: str(selected[key]) for key in ('work', 'output', 'disk', 'checks', 'source_lock', 'qmp')})
    if previous is not None:
        archive = strict(root, Path(archive_output) / ('previous-active-build-' + nonce + '.json'))
        with archive.open('xb') as destination:
            destination.write(previous)
    pending = strict(root, target.parent / ('active-build.pending-' + nonce + '.json'))
    with pending.open('xb') as destination:
        destination.write((json.dumps(record, sort_keys=True, indent=2) + '\n').encode())
        destination.flush()
        os.fsync(destination.fileno())
    current = read_control(root, target) if target.exists() else None
    if current != previous:
        raise ValueError('Builder descriptor changed before publication; pending record retained')
    pending.replace(target)
    return record
