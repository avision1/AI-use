#!/usr/bin/env python3
"""Guest-only verified archive import, guarded recovery and public lb chroot.

No ISO, installer, binary or source stage is run or certified by this helper.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

BUILD = Path('/root/windows12-build')
ROOT = BUILD / 'chroot'
OUT = Path('/project-output')
HELPERS = {'inspection': Path('/root/windows12-inspection.py'),
           'recovery': Path('/root/windows12-recover.py'),
           'importer': Path('/root/windows12-import.py')}
HEX = re.compile(r'[0-9a-f]{64}')
CHILD_LOG_LIMIT = 64 * 1024 * 1024
OPTIONS = '--yes -o Acquire::Retries=5 --no-download'
OVERLAY = ('APT_OPTIONS="' + OPTIONS + '"\n').encode()
ARCHIVE_SHA = '1aad324e433d6cb6d038193252b74fd0ed1c1e1d7e1c6cf410c8fb09c5225b9e'
SOURCE_PINS = {'/usr/bin/lb': '3dead87e114a90ca11953edc362435bc69771c72e7d3f28dc92d1f16656d66d6',
 '/usr/lib/live/build.sh': '5bc21c1ff13097f516f66189288172536c0efddde011bb45f2489dfd2439ba8e',
 '/usr/lib/live/build/binary': '386136aab20e27cf9b87dfa605c1d729b031a840334349f044a83cc5d1bcab50',
 '/usr/lib/live/build/binary_bootloader_splash': '08bac3ce6eefd694e3a75ffadf483fe7a3c099337ea2c99cf6955f138147ea50',
 '/usr/lib/live/build/binary_checksums': 'ebd57da0fc182ce2f9be265e64821c7a7c6e747481d40527c5b2342b7622bfc0',
 '/usr/lib/live/build/binary_chroot': 'aeabd4229122630ebdf5a9b3a91817ba28d2f07758a83dfd61c7d5106f6df8ac',
 '/usr/lib/live/build/binary_disk': '40f2cc333c09788b1c9da4c24f33e7f7e57c518775df67dbf811df7296677314',
 '/usr/lib/live/build/binary_dm-verity': '4009710960c00f4b9525096b698526b38f27aad8ffcd748fadc4e4895925b85c',
 '/usr/lib/live/build/binary_grub-efi': 'ca39f80942d33488792512152231cd27a866379cf2e8e040631188a0ffb4236e',
 '/usr/lib/live/build/binary_grub-legacy': '2b5bd35118d024901acbc6f43c053830c9ebac422ce545fddccf65622fc9a95b',
 '/usr/lib/live/build/binary_grub-pc': 'e15813c703b9d803af7e2c1d42ef667e0c678bd04f5016da34209a21225fc674',
 '/usr/lib/live/build/binary_grub_cfg': '306c7e54686e5d97285525eb6161cd62291d1c06424fabfcd3d754c283d79b9e',
 '/usr/lib/live/build/binary_hdd': 'f0176b2851a9cbe1cbfc295b1fd911b587a1732aa7bb2bd315bb50172df44038',
 '/usr/lib/live/build/binary_hooks': 'acb7096de1695e48fdab397768fc8a147b48860b3bf523a36e12b1241e60556a',
 '/usr/lib/live/build/binary_includes': 'd936bb5db8f1d52a5af032266ea002cc91e42fad204110eb1185121182dc5956',
 '/usr/lib/live/build/binary_iso': '396a68c7d86d1b660a493d9d307fcd53dfee3cfafcbb9840779a4a2742b99959',
 '/usr/lib/live/build/binary_linux-image': 'e79ce5feaa66bae2606500414ddf03fc6bb438e3eab19392030d0f9d17acb710',
 '/usr/lib/live/build/binary_loadlin': '8e40c897664244b73053e16acb463810d0b2c75342852cc1e0ca26b0edfe60ef',
 '/usr/lib/live/build/binary_manifest': 'e8d31853ead3b8b01c975e48776811909455233bc9187999242b268b5c5f5bb2',
 '/usr/lib/live/build/binary_memtest': '5b5cedec3e38afcf7987ff904fadf97bbbb487672f4b56ec78aa594da10985ef',
 '/usr/lib/live/build/binary_netboot': '52d8846ceacc331b67400d9758ae28d0a59485c7f33a3f02641cb0153b7fba5e',
 '/usr/lib/live/build/binary_onie': '0411fcb39a7a09355691baaf78dd1f0af57c92fcec5db47a8e568c24693aa50b',
 '/usr/lib/live/build/binary_package-lists': 'e33b6f487a9afec3aecf25334ae39639e69becdae2e4d3352f7d75a2c5468113',
 '/usr/lib/live/build/binary_rootfs': 'e6498a5c69ea21660005854ee37c6a5634a9a8448ed5e32a308b647318e2f12b',
 '/usr/lib/live/build/binary_syslinux': '35e9aaa61cf48f5a75f92095b3dd34840f7f6519787b33143c0ab1b3b5c9c2ed',
 '/usr/lib/live/build/binary_tar': 'd394ff0e27c16dd15f281a305cffef7394f3c5cc8e8437e99c6c1da7f48c2762',
 '/usr/lib/live/build/binary_win32-loader': 'bb285c83e5b5b3df3a2fac232c0d6e9b9fe3edea49d255fdb30980ebcbed134a',
 '/usr/lib/live/build/binary_zsync': 'a4e0a3eb42324d691c04cd1e5a09bd9871fa9926dfcb68e7f53124d09ffe4e90',
 '/usr/lib/live/build/bootstrap': 'f12a5e4e113cf85a0c96a1064e16e154c4c6d18a77f9af73fb9ff8e87e963b60',
 '/usr/lib/live/build/bootstrap_cache': '299df8cc92f69e036c600eec599213a2e7deaff392dcab648255abc56e0b1f09',
 '/usr/lib/live/build/bootstrap_debootstrap': '0397f1e77a01f82d83cbf479cf63954c1eb138c8cbba721247f93b03341db8a3',
 '/usr/lib/live/build/build': '79d5b86f0c16b2ff060f8a8669eea214412dda481692d751c65d23480fc4717e',
 '/usr/lib/live/build/chroot': 'abd9f5fae349d4e9a56300899861e12f891cdfb7abf44c5a4a203d6ea0ca8dd4',
 '/usr/lib/live/build/chroot_apt': 'f8a6dab0276caba6931c4e4866cdf4cd640c1d4177f9f759fb7cde7b2823125d',
 '/usr/lib/live/build/chroot_archives': 'ec430b43463d06183c22cf982969b9f2bbbfbe85eea8da1295faa9b1843b9415',
 '/usr/lib/live/build/chroot_cache': '7f9801543e735aba87fa66ebd4f906ebe8dd5d6eca90b229b32eb7c4b03f98e1',
 '/usr/lib/live/build/chroot_debianchroot': '4f04bd7f24427cb9f57a7836afea15bff0e396cd68f723cfe97059bbf1f4eaf9',
 '/usr/lib/live/build/chroot_devpts': 'ee0c021410ea095071047b08c8b82423ee41f922e23997f580c8404d28722f3c',
 '/usr/lib/live/build/chroot_dpkg': '4e419d6e97498f2a51312ec19e93699719dc28a3a3321beceb1f984eaa4b230f',
 '/usr/lib/live/build/chroot_firmware': '4ced17271a32ff755fa2705d4c9848c3d2cb4247a30c6e0c4b03a7ca8511180c',
 '/usr/lib/live/build/chroot_hacks': '1dac3a0aee51d35119aa649cf3001faac31dbbe940cc847fe8d4695033607dc9',
 '/usr/lib/live/build/chroot_hooks': '2dd0561274b1011e2f8f998c9c9e5f61855355f2b9c5b9289c1816427fca8ae3',
 '/usr/lib/live/build/chroot_hostname': 'd330d4b0e1c8388d56d7beb82a2a23b621a7e0fa787a0554b05a33d7b1296852',
 '/usr/lib/live/build/chroot_hosts': 'cb06ec0ee979b305e47c35189f6447c88562c729f36853fe5a80817bf2171097',
 '/usr/lib/live/build/chroot_includes_after_packages': 'bb659e92c954abb188c0899f204a5e6c3654ec07b433c2806fa982b02df08a26',
 '/usr/lib/live/build/chroot_includes_before_packages': '3853ebc201c67f5438cd58649bb210b608401296fe58df33308bf88095b99d29',
 '/usr/lib/live/build/chroot_install-packages': '64e6621e6478ceebc1268e83d1a37a8fc874691d70cab9cdb2be53c899c66f8f',
 '/usr/lib/live/build/chroot_interactive': '865e7629669328ba6e2dd60a3d62301637bc837ba8d3d03967625cae1dd0d48b',
 '/usr/lib/live/build/chroot_linux-image': 'f320b9dc6a5b91480637d503f491f89c72757d60172edb5ec237ba51e632220e',
 '/usr/lib/live/build/chroot_package-lists': '988536b0a678e44eba9dbf2f9177e505ca78aeb2dfe113ce592b526210e2a87c',
 '/usr/lib/live/build/chroot_prep': '98ccba668f5f69edd19aa28604d4d9e467554b3dc49b5a2ec99d452cd0530513',
 '/usr/lib/live/build/chroot_preseed': '72625cfb70dc0dfcdfcf555dc4f35fc0b85e60ccde45f18009625bdc9b915801',
 '/usr/lib/live/build/chroot_proc': 'e497f7935b30e0700c219f34196893f2ddb0bf8cd6982477f8f2441de218a576',
 '/usr/lib/live/build/chroot_resolv': '6d859f81ed4a3b9abb7963eac2eb1f9f3629fde4671f38c163504fa0a5fa4004',
 '/usr/lib/live/build/chroot_selinuxfs': '70366b7b1681b89532b7dba9159d9cbf6ab7152f351089af2812221e68622a6a',
 '/usr/lib/live/build/chroot_sysfs': '32efd609a34660a69a6e037d62d428b687a513dad5c2622b790dd2c1697e2647',
 '/usr/lib/live/build/chroot_sysv-rc': '478fcf6f06eda8fa1236449eeb032a4d2e305cbb0e7b8f73b4696a80c468c17d',
 '/usr/lib/live/build/chroot_tmpfs': '26f648a3e9a73ce74e30d14f6a443f33b172172545a56fd411ce03d40c020e47',
 '/usr/lib/live/build/clean': '2d582bee71872bea8912d3939ff1fbb1b1470831730dc18d951ade2c8e425c7b',
 '/usr/lib/live/build/config': 'e5f2e6ab7b20e2c02ac3a089c97a5a9c553f485cb26e3511e7df8c485bde5785',
 '/usr/lib/live/build/efi-image': '4b80b1b9c4a86f23fc676ac4f2ee5e9d3d25b59ccd4d2be487be584c385f606d',
 '/usr/lib/live/build/grub-cpmodules': 'ab22ce958451bd852ce27e8bb3fb01d9a736a512f36de1c356a79bc04e330618',
 '/usr/lib/live/build/installer': '9fc5b0e50b3a4030ef69260d5a088e3097a8e0f732b7c50d54a675aa81fdf81c',
 '/usr/lib/live/build/installer_chroot': '723cb6ba4cdcb3ea45e06a70936b10847b2196d52e61335bd3df4a1b8d26ee90',
 '/usr/lib/live/build/installer_debian-installer': '20a23b6625e3cbd7f38f28fc36d78dd664ec3ca1d82041e221d2ce90c78afd0b',
 '/usr/lib/live/build/installer_preseed': '424c5e25eaa78078a642117df0af2fc282a55a0991c958061fa2b1d6074cd17b',
 '/usr/lib/live/build/source': 'c4ea4653b851acb56cef5cd0089ff475ffc481afabf5829d1023729a1be5c9fd',
 '/usr/lib/live/build/source_checksums': 'de7d8136688ca36d1df1473bd00e6d9935a039a9d8c1d82f0a19b3abb7921447',
 '/usr/lib/live/build/source_debian': '25a7686177193649a3e7df07d5e7b659d920e7657348735574d65f4ea775f30d',
 '/usr/lib/live/build/source_disk': '1f8a3d9b09523abc0dc98e47a83d46681c8493641986ee85df9cd6e5efb3027d',
 '/usr/lib/live/build/source_hdd': '887e20172ebdd7852ca2ae7d3f0c10ea3712946533c7c14594c0ad54b77933c5',
 '/usr/lib/live/build/source_hooks': '15ace516cb0726888ea2c6eb8645e9ef30f99973dd6107565812870dd08da74e',
 '/usr/lib/live/build/source_iso': '3cc899e657f841d794f57f248dacacec9f32408be47b5e5a8a410d303e37963a',
 '/usr/lib/live/build/source_live': '15710675599da836f37c4029981e326e2f73fe10fafbcc81f02f30f0d07a6e74',
 '/usr/lib/live/build/source_tar': '0806f76ea2f49db8b1f1889d10d59659728873624a2a05a1b90522a609f0e739',
 '/usr/share/live/build/functions/aliases.sh': '9b08bee415a85da3d1585b29ba4d30279a1cca514fe2e10b51298a9d5da2f78a',
 '/usr/share/live/build/functions/arguments.sh': '09a567624f6c1d235e00d6f94bdf0062249a5973867f6e25e5f07699525f0033',
 '/usr/share/live/build/functions/breakpoints.sh': '7a353afe34e14c5426806301b7b5df8fd705b6767ad2b2a5937bc05d9701b79c',
 '/usr/share/live/build/functions/cache.sh': '977a54223a7c41593c551c8067f0c20e61d9e3e53ebed5889669a1761e3c4b3f',
 '/usr/share/live/build/functions/chroot.sh': 'a4590942d39d2d2115ab4b93cf7779e0fad18564810128dad663e296ab842852',
 '/usr/share/live/build/functions/chroot_bind_path.sh': 'c14425c72b653ba9dbbfff9800af94c9b838a6e35418501c15ecb232067cbb8a',
 '/usr/share/live/build/functions/color.sh': 'df424c93a57a0fec9883b61e4971db0dbffa8992568cf241c643bc39f5787b61',
 '/usr/share/live/build/functions/common.sh': 'dad938d06bc038a800cfd9445c7c2a03d46a39bb329fc5a0f2c2dd230b9e8773',
 '/usr/share/live/build/functions/compatibility.sh': '9d738f3261515dc456df212fdb826bf3ece3402f165874bad3abf48fc1b512f5',
 '/usr/share/live/build/functions/conffile.sh': '17470ba72dba44d564b33c37d37e871516517d05826a53c3f7d137d664fbbc6b',
 '/usr/share/live/build/functions/configuration.sh': 'e83601d40be86f5048198509d86cce5b031fdc53dc76a0b85087df1dde708a40',
 '/usr/share/live/build/functions/echo.sh': '20d8522a227067738b7d547515c1c8faafd780e671f26ed636466d5755e0ee80',
 '/usr/share/live/build/functions/exit.sh': '7832fcf7b60660c1e64b8201d4257a7de7a0e12525205e8bd8cb7c8145fb67ff',
 '/usr/share/live/build/functions/firmwarelists.sh': 'a26192ca6c5d310554867be7fbaf09ab358c6519f06878beb9e9074afb1379ad',
 '/usr/share/live/build/functions/init.sh': '61bdddb1b722b8cdd6bd7040ebaeaa610d528110bf06f5ef14d3baf20891516c',
 '/usr/share/live/build/functions/lockfile.sh': 'cacc640cdd247ed08db84c11e62b96015752b4848c34e5efc307d07581d9d880',
 '/usr/share/live/build/functions/losetup.sh': '6efc7c921e6f200179e7727fc96e35c9bab92cf333ad08474520409fe4f34ac2',
 '/usr/share/live/build/functions/man.sh': '86982ed43641033b49ed0319062b11e470254c8c2099f3b4891f0aecdefebb01',
 '/usr/share/live/build/functions/packagelists.sh': 'af2ba8f7c07c762a9f7dc3f83669ab53581f47081d1bcceba23866a629eca733',
 '/usr/share/live/build/functions/packages.sh': 'd286ccd88ff6ed1d25e26b220f4d026639b394a23087abcffb984507dfeebb04',
 '/usr/share/live/build/functions/sourcelist.sh': '04f62586abb44db6abf533fc838f8668ea671c2c4ec580847835ff4d568e33cc',
 '/usr/share/live/build/functions/stagefile.sh': 'aa66b2ec9f1443c8a7c39683bad778a3f5753a73e1af28fb14b0855152ce277f',
 '/usr/share/live/build/functions/usage.sh': 'e097a9edddf21eb19beeea9632ea25db8943b8830a945551fcc7ba675660fea6',
 '/usr/share/live/build/functions/wrapper.sh': 'fbd61ab586b5db95fc4ac4edd7e6995154b3dd6c40df9c91e5de1c5b665e7563'}
CONFIG_PINS = {'binary': 'b16bcd609986cf369283406e68ab4e550acf7689788edb36e258bf7dc20b0a55',
 'bootstrap': 'a4bce96a1a100177de14a56ce567484b1583f01315e5d1cc4a34fc4a1cc64397',
 'chroot': 'cb6e2dd1c4fd0d08812e4925124a523594981afbc78fb329841f254c95b3ccc1',
 'common': '441614d494379408f1eae97f4aafacc67759dc774487250ac90d1a34c8fc45d6',
 'source': 'b26d96ae9450d13e2df09e7729ee36c9d3f431b7c7c64d2066e6a13b8f2f0ff4'}
INITIAL = {'config', 'bootstrap', 'bootstrap_cache.save', 'chroot_apt',
           'chroot_debianchroot', 'chroot_dpkg', 'chroot_hostname', 'chroot_hosts',
           'chroot_resolv', 'chroot_sysv-rc', 'chroot_archives', 'chroot_firmware',
           'chroot_includes_before_packages', 'chroot_linux-image',
           'chroot_package-lists.install', 'chroot_preseed'}
RUNTIME = {'chroot_devpts', 'chroot_proc', 'chroot_selinuxfs', 'chroot_sysfs', 'chroot_tmpfs'}
CORE = ('plasma-desktop', 'plasma-workspace', 'sddm', 'dolphin', 'plasma-discover',
        'calamares', 'calamares-settings-debian', 'chromium', 'firefox-esr',
        'libreoffice-writer', 'libreoffice-calc', 'libreoffice-impress',
        'network-manager', 'plasma-nm', 'python3', 'xdg-utils', 'linux-image-amd64')
# Probe invokes only the pinned pure configuration reader. No Arguments,
# Prepare_config, stage helper, target binary, mount or package operation.
PROBE = r'''set -eu
. /usr/share/live/build/functions/conffile.sh
Echo_debug () { :; }
Echo_warning () { exit 92; }
Read_conffiles $(Common_conffiles)
printf '%s\n' "$APT_OPTIONS" "$LB_APT" "$LB_ARCHITECTURE" "$LB_DISTRIBUTION" "$LB_CACHE" "$LB_CACHE_PACKAGES" "${LB_BUILD_WITH_TMPFS:-false}" "${LB_INITRAMFS:-live-boot}"
'''


def canonical(path, missing=False):
    path = Path(path)
    if not path.is_absolute() or str(path) != os.path.normpath(str(path)):
        raise ValueError('Noncanonical path')
    for part in reversed((path, *path.parents)):
        try:
            s = part.lstat()
        except FileNotFoundError:
            if missing:
                continue
            raise
        if stat.S_ISLNK(s.st_mode) or (part != path and not stat.S_ISDIR(s.st_mode)):
            raise ValueError('Aliased path: ' + str(part))
    return path


def read(path, limit=1024 * 1024):
    path = canonical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != 0 or before.st_nlink != 1
                or before.st_size > limit or before.st_mode & 0o022):
            raise ValueError('Unsafe bounded root-owned input: ' + str(path))
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_uid', 'st_gid', 'st_nlink')
    if len(data) > limit or any(getattr(before, k) != getattr(after, k) for k in fields) or path.lstat() != after:
        raise ValueError('Input changed or exceeds bound: ' + str(path))
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def absent(path):
    path = canonical(path, missing=True)
    if path.exists():
        raise ValueError('Unexpected prior or override path: ' + str(path))


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def load(path, limit):
    raw = read(path, limit)
    return json.loads(raw, object_pairs_hook=unique), digest(raw)


def sync(directory):
    fd = os.open(canonical(directory), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def newfile(path, data):
    canonical(path, missing=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    sync(path.parent)


def report_write(report, workspace, publish=True):
    raw = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
    if len(raw) > 1024 * 1024:
        raise ValueError('Result exceeds 1 MiB')
    targets = [workspace / 'result.json']
    if publish:
        targets.append(OUT / 'package-stage-result.json')
    for target in targets:
        canonical(target, missing=True)
        if target.exists():
            read(target, 1024 * 1024)
        temporary = workspace / 'result-next.json'
        newfile(temporary, raw)
        os.replace(temporary, target)
        sync(target.parent)



def preserve_previous(report, workspace):
    # Only these fixed evidence names are eligible. Everything else in OUT,
    # especially plan/catalog/audit/refresh evidence, is left in place.
    limits = {'package-cache-import.json': 32 * 1024 * 1024,
              'builder-recovery.json': 256 * 1024,
              'package-stage-result.json': 1024 * 1024,
              'package-stage.packages': 8 * 1024 * 1024}
    previous = workspace / 'previous'
    absent(previous)
    previous.mkdir(mode=0o700)
    sync(workspace)
    records = []
    for name, bound in limits.items():
        source = canonical(OUT / name, missing=True)
        if not source.exists():
            continue
        before = source.lstat()
        raw = read(source, bound)
        if source.lstat() != before or before.st_dev != previous.stat().st_dev:
            raise ValueError('Prior proof changed or crosses filesystems')
        # Top-level evidence carrying this fresh nonce would establish reuse,
        # even if someone had previously removed its nonce workspace.
        if name.endswith('.json'):
            old = json.loads(raw, object_pairs_hook=unique)
            if not isinstance(old, dict):
                raise ValueError('Prior report is not a JSON object')
            if any(old.get(key) == report['nonce'] for key in ('nonce', 'recovery_nonce', 'inspection_nonce')):
                raise ValueError('Fresh nonce already occurs in prior report')
        records.append({'source': str(source), 'destination': str(previous / name),
                        'bytes': len(raw), 'sha256': digest(raw), 'status': 'pending',
                        'metadata': {k: getattr(before, k) for k in
                                     ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_uid', 'st_gid',
                                      'st_nlink', 'st_mtime_ns', 'st_ctime_ns')}})
    report['previous_proofs'] = records
    report_write(report, workspace, publish=False)
    library = ctypes.CDLL(None, use_errno=True)
    rename = library.renameat2
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    for record in records:
        source = canonical(record['source'])
        target = Path(record['destination'])
        absent(target)
        raw = read(source, limits[source.name])
        current = source.lstat()
        if (digest(raw) != record['sha256'] or len(raw) != record['bytes']
                or any(getattr(current, key) != value for key, value in record['metadata'].items())):
            raise ValueError('Prior proof changed immediately before preservation')
        # Atomic RENAME_NOREPLACE, same filesystem only, no fallback or clobber.
        if rename(-100, os.fsencode(source), -100, os.fsencode(target), 1) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), str(source))
        sync(OUT)
        sync(previous)
        after = target.lstat()
        if (digest(read(target, limits[source.name])) != record['sha256']
                or any(getattr(after, key) != value for key, value in record['metadata'].items()
                       if key != 'st_ctime_ns')):
            raise ValueError('Preserved proof bytes or identity differ')
        record['status'] = 'preserved'
        report_write(report, workspace, publish=False)
    for name in limits:
        absent(OUT / name)


def flags():
    directory = canonical(BUILD / '.build')
    entries = list(directory.iterdir())
    if len(entries) > 256:
        raise ValueError('Stage inventory exceeds bound')
    result = set()
    for p in entries:
        if read(p, 0) != b'':
            raise ValueError('Nonempty stage flag')
        result.add(p.name)
    return result


def quiet():
    mounts = Path('/proc/self/mountinfo').read_bytes()
    if len(mounts) > 2 * 1024 * 1024:
        raise ValueError('Oversized mount inventory')
    for line in mounts.splitlines():
        fields = line.split()
        if len(fields) > 4 and (fields[4] == bytes(BUILD) or fields[4].startswith(bytes(BUILD) + b'/')):
            raise ValueError('Active build mount')
    processes = list(Path('/proc').iterdir())
    if len(processes) > 32768:
        raise ValueError('Oversized process inventory')
    banned = {'lb', 'live-build', 'apt', 'apt-get', 'aptitude', 'dpkg', 'dpkg-deb', 'debootstrap'}
    for p in processes:
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            with (p / 'cmdline').open('rb') as stream:
                raw = stream.read(65537)
        except FileNotFoundError:
            continue
        if len(raw) > 65536:
            raise ValueError('Oversized process command')
        args = raw.decode(errors='replace').split('\0')
        if any(Path(a).name in banned or a.startswith('/usr/lib/live/build/') for a in args):
            raise ValueError('Active package/build process: ' + p.name)


def helper_pins(args):
    for name, path in HELPERS.items():
        if digest(read(path, 128 * 1024)) != getattr(args, name + '_sha256'):
            raise ValueError('Controller helper pin differs: ' + name)


def initial_status():
    if digest(read(ROOT / 'var/lib/dpkg/status', 32 * 1024 * 1024)) != 'cf0bdc5bd7e2c0332cb2906f099c044077321f6583fc4eb45eac7d452b2c91e8':
        raise ValueError('Exact reviewed pre-install status required')
    h = hashlib.sha256()
    paths = sorted(canonical(ROOT / 'var/lib/dpkg/info').glob('*.md5sums'))
    if len(paths) != 144:
        raise ValueError('Exact reviewed checksum metadata count required')
    total = 0
    for p in paths:
        data = read(p, 2 * 1024 * 1024)
        total += len(data)
        h.update(p.name.encode() + b'\0' + data + b'\0')
    if total != 450161 or h.hexdigest() != '1dfcd7999383a91e54e9cec6729910adcabde8b22f102c81294a239bcfc8bb76':
        raise ValueError('Exact reviewed checksum metadata required')


def sources():
    for path, sha in SOURCE_PINS.items():
        if digest(read(path)) != sha:
            raise ValueError('Installed live-build source differs: ' + path)
    directory = canonical('/usr/share/live/build/functions')
    actual = {str(p) for p in directory.glob('*.sh')}
    expected = {p for p in SOURCE_PINS if p.startswith(str(directory) + '/')}
    if actual != expected:
        raise ValueError('Function loader membership differs')
    if read('/usr/share/live/build/VERSION', 128) != b'20250505+deb13u1\n':
        raise ValueError('Wrong live-build VERSION')
    # Empty LIVE_BUILD resolves the loader's two absolute fallback probes.
    for path in ('/functions', '/scripts/build.sh'):
        absent(path)
    absent(BUILD / 'local/live-build')


def configurations():
    common = ['config/' + n for n in ('all', 'common', 'bootstrap', 'chroot', 'binary', 'source')]
    sequence = common + [p + suffix for p in common for suffix in ('.amd64', '.trixie')]
    # No unreviewed effective input is sourced, even when present but empty.
    for path in sequence:
        p = BUILD / path
        name = p.name
        if name in CONFIG_PINS:
            if digest(read(p)) != CONFIG_PINS[name]:
                raise ValueError('Saved config hash differs: ' + path)
        else:
            absent(p)
    for name in ('environment', 'environment.binary'):
        absent(BUILD / 'config' / name)
    for name in ('config', 'build', 'chroot', 'installer', 'binary', 'source', 'clean'):
        absent(BUILD / 'auto' / name)
    return sequence


def inherited_environment():
    allowed = {'LB_CACHE': 'false', 'LB_CACHE_INDICES': 'false', 'LB_CACHE_PACKAGES': 'false',
               'LB_CACHE_STAGES': 'bootstrap', 'LB_BUILD_WITH_TMPFS': 'false', 'LB_MODE': 'debian',
               'LB_SYSTEM': 'live', 'LB_ARCHITECTURE': 'amd64', 'LB_DISTRIBUTION': 'trixie',
               'LB_DISTRIBUTION_CHROOT': 'trixie', 'LB_DISTRIBUTION_BINARY': 'trixie',
               'LB_DEBIAN_INSTALLER': 'live'}
    for name, value in os.environ.items():
        if name.startswith('LB_') and (name not in allowed or value != allowed[name]):
            raise ValueError('Unreviewed LB environment: ' + name)
        if (name.startswith(('APT_', 'APTITUDE_', 'LD_', 'PYTHON', 'BASH_FUNC_'))
                or name in {'LIVE_BUILD', '_FORCE', 'CONFIG_VALIDATED', 'ENV', 'BASH_ENV', 'SHELLOPTS', 'CDPATH'}):
            raise ValueError('Loader/options environment override: ' + name)


def environment(workspace):
    return {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': str(workspace),
            'TMPDIR': str(workspace), 'XDG_CACHE_HOME': str(workspace),
            'LC_ALL': 'C', 'LANG': 'C', 'PYTHONDONTWRITEBYTECODE': '1',
            'LB_ARCHITECTURE': 'amd64', 'LB_DISTRIBUTION': 'trixie'}


def write_all(stream, block):
    remaining = memoryview(block)
    while remaining:
        written = stream.write(remaining)
        if not isinstance(written, int) or written <= 0 or written > len(remaining):
            raise OSError('Child output sink made no valid write progress')
        remaining = remaining[written:]


def stop_owned_child(child):
    # Popen creates a new session: the group ID is this owned child's PID.
    # On observation failure terminate the entire group, not just the lb shell,
    # so inherited APT/dpkg children cannot continue unobserved.
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    try:
        # Also kill surviving descendants when the group leader exited early.
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    finally:
        child.wait()


def invoke(argv, env, log):
    # argv is constructed only from fixed paths, validated hex or fixed switches.
    # No stage timeout: actual public package installation may take hours.
    console = sys.stdout.buffer
    newfile(log, b'')
    fd = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    with os.fdopen(fd, 'ab', buffering=0) as stream:
        child = subprocess.Popen(argv, cwd=BUILD, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 start_new_session=True, close_fds=True, bufsize=0)
        total = 0
        try:
            while True:
                block = child.stdout.read(64 * 1024)
                if not block:
                    break
                if total + len(block) > CHILD_LOG_LIMIT:
                    raise ValueError('Child output exceeds bounded 64 MiB log')
                write_all(stream, block)
                total += len(block)
                write_all(console, block)
                console.flush()
            code = child.wait()
            os.fsync(stream.fileno())
            return code
        except BaseException:
            stop_owned_child(child)
            raise
        finally:
            child.stdout.close()


def transport(env):
    completed = subprocess.run(['/bin/sh', '-c', PROBE], cwd=BUILD, env=env,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=30, check=False)
    # These are values after the exact complete ordered configuration read.
    expected = (OPTIONS + '\napt\namd64\ntrixie\nfalse\nfalse\nfalse\nlive-boot\n').encode()
    if completed.returncode or completed.stdout != expected or completed.stderr:
        raise ValueError('Exact configuration option transport probe failed')
    return {'returncode': 0, 'stdout': completed.stdout.decode(), 'stderr': '',
            'scope': 'pinned Read_conffiles only; no install or target execution'}


def installed_manifest(workspace):
    raw = read(ROOT / 'var/lib/dpkg/status', 32 * 1024 * 1024)
    records = []
    names = set()
    versions = {}
    for paragraph in raw.decode('utf-8').split('\n\n'):
        if not paragraph.strip():
            continue
        fields = {}
        for line in paragraph.splitlines():
            if line.startswith((' ', '\t')):
                continue
            key, sep, value = line.partition(':')
            if not sep or not re.fullmatch(r'[A-Za-z0-9-]+', key) or key in fields:
                raise ValueError('Malformed target status record')
            fields[key] = value.lstrip(' ')
        if fields.get('Status') != 'install ok installed':
            raise ValueError('Target has a non-installed package record')
        package, architecture, version = (fields.get(k, '') for k in ('Package', 'Architecture', 'Version'))
        if (not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', package)
                or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', architecture)
                or not re.fullmatch(r'[A-Za-z0-9.+:~_-]+', version)):
            raise ValueError('Malformed package/version/architecture')
        identity = package + ':' + architecture
        if identity in names:
            raise ValueError('Duplicate installed package identity')
        names.add(identity)
        records.append((identity, version))
        versions.setdefault(package, []).append(version)
    if any(len(versions.get(p, [])) != 1 for p in CORE):
        raise ValueError('Core package missing or ambiguous')
    output = ''.join(p + '\t' + v + '\n' for p, v in sorted(records)).encode()
    path = OUT / 'package-stage.packages'
    newfile(path, output)
    newfile(workspace / 'package-stage.packages', output)
    return {'path': str(path), 'sha256': digest(output), 'bytes': len(output),
            'packages': len(records), 'target_status_sha256': digest(raw),
            'core_package_versions': {p: versions[p][0] for p in CORE},
            'method': 'read-only target dpkg status parsing; no target executable'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('nonce', 'plan-nonce', 'manifest-sha256', 'inspection-sha256', 'recovery-sha256', 'importer-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if (not all(re.fullmatch(r'[0-9a-f]{32}', n) for n in (args.nonce, args.plan_nonce))
            or args.nonce == args.plan_nonce
            or not all(HEX.fullmatch(getattr(args, k)) for k in
                       ('manifest_sha256', 'inspection_sha256', 'recovery_sha256', 'importer_sha256'))):
        raise ValueError('Fresh nonce32, distinct original plan nonce32 and exact SHA256 pins required')
    if os.geteuid() != 0:
        raise ValueError('Contained guest root required')
    read('/run/windows12-build-vm', 4096)
    for p in (BUILD, ROOT, OUT):
        canonical(p)
        if not p.is_dir():
            raise ValueError('Required fixed directory missing')
    if Path.cwd() != BUILD:
        raise ValueError('Fixed BUILD working directory required')
    inherited_environment()
    helper_pins(args)
    initial_status()
    sources()
    sequence = configurations()
    quiet()
    initial = flags()
    if not INITIAL.issubset(initial) or initial - INITIAL - (RUNTIME - {'chroot_tmpfs'}):
        raise ValueError('Expected exactly sixteen completed flags and optional reviewed runtime flags')
    workspace = OUT / ('package-stage-' + args.nonce)
    absent(workspace)
    for previous_nonce_path in (OUT / ('package-cache-import-' + args.nonce),
                                OUT / ('builder-recovery-quarantine-' + args.nonce),
                                BUILD / ('package-cache-staging-' + args.nonce)):
        absent(previous_nonce_path)
    workspace.mkdir(mode=0o700)
    sync(OUT)
    report = {'schema': 1, 'nonce': args.nonce, 'plan_nonce': args.plan_nonce,
              'manifest_sha256': args.manifest_sha256, 'started': time.time(),
              'chroot_completed': False, 'iso_verified': False,
              'child_log_limit_bytes': CHILD_LOG_LIMIT,
              'native_apt_cached_sha256_verified': False,
              'native_apt_cached_sha256_reason': 'APT 3.0.3 cached archive hit checks size only; importer hashes all authenticated full transaction bytes',
              'expected_apt_options': OPTIONS, 'source_archive_sha256': ARCHIVE_SHA,
              'source_pins': SOURCE_PINS, 'helper_pins': {n: getattr(args, n + '_sha256') for n in HELPERS},
              'outcome': 'preflight'}
    env = environment(workspace)
    reports_ready = False
    try:
        report_write(report, workspace, publish=False)
        native = subprocess.run(['/usr/bin/dpkg-query', '-W', '-f=${Version}', 'live-build'],
                                env=env, cwd=BUILD, capture_output=True, timeout=30, check=False)
        if native.returncode or native.stdout != b'1:20250505+deb13u1' or native.stderr:
            raise ValueError('Builder native live-build package version differs')
        overlay = workspace / 'offline-options'
        newfile(overlay, OVERLAY)
        env['LB_CONFIG'] = ' '.join(sequence + [str(overlay)])
        report['configuration_order'] = sequence + [str(overlay)]
        report['options_file'] = {'path': str(overlay), 'sha256': digest(OVERLAY), 'bytes': len(OVERLAY)}
        report['transport_probe'] = transport(env)
        helper_pins(args)
        initial_status()
        sources()
        configurations()
        quiet()
        if flags() != initial:
            raise ValueError('Stage state changed during complete preflight')
        preserve_previous(report, workspace)
        reports_ready = True
        report_write(report, workspace)
        # Import first: its exact plan provenance includes nineteen or sixteen
        # flags. Recovery intentionally changes that provenance afterwards.
        helperenv = environment(workspace)
        helper_pins(args)
        rc = invoke(['/usr/bin/python3', '-B', str(HELPERS['importer']), '--nonce', args.nonce,
                     '--plan-nonce', args.plan_nonce, '--manifest-sha256', args.manifest_sha256],
                    helperenv, workspace / 'import.log')
        report['import_returncode'] = rc
        report_write(report, workspace)
        imported, sha = load(OUT / 'package-cache-import.json', 32 * 1024 * 1024)
        report['import_proof'] = {'sha256': sha, 'returncode': rc, 'path': str(OUT / 'package-cache-import.json')}
        if (rc or imported.get('nonce') != args.nonce or imported.get('plan_nonce') != args.plan_nonce
                or imported.get('manifest_sha256') != args.manifest_sha256
                or imported.get('final_selected_sha256_verified') is not True
                or imported.get('final_verified_archive_count') != len(imported.get('files', []))
                or imported.get('import_performed') is not True or imported.get('preserved_target') is not True
                or not imported.get('files') or any(p.get('status') not in {'already-verified', 'published-verified'} for p in imported['files'])):
            raise ValueError('Full authenticated archive import failed')
        report_write(report, workspace)
        sources()
        configurations()
        quiet()
        helper_pins(args)
        rc = invoke(['/usr/bin/python3', '-B', str(HELPERS['recovery']), '--nonce', args.nonce,
                     '--inspection-sha256', args.inspection_sha256, '--package-stage'],
                    helperenv, workspace / 'recovery.log')
        report['recovery_returncode'] = rc
        report_write(report, workspace)
        recovered, sha = load(OUT / 'builder-recovery.json', 256 * 1024)
        report['recovery_proof'] = {'sha256': sha, 'returncode': rc, 'path': str(OUT / 'builder-recovery.json')}
        if (rc or recovered.get('recovery_nonce') != args.nonce or recovered.get('package_stage') is not True
                or recovered.get('recovery_performed') is not True or flags() != INITIAL):
            raise ValueError('Exact package-stage recovery failed')
        report_write(report, workspace)
        sources()
        configurations()
        quiet()
        if read(overlay, 4096) != OVERLAY:
            raise ValueError('Private final options changed')
        helper_pins(args)
        report['transport_probe_before_lb'] = transport(env)
        report['outcome'] = 'public-chroot-running'
        report_write(report, workspace)
        rc = invoke(['/usr/bin/lb', 'chroot'], env, workspace / 'lb-chroot.log')
        report['public_chroot_returncode'] = rc
        report_write(report, workspace)
        if rc:
            raise ValueError('Public lb chroot failed; retained partial state requires review')
        quiet()
        absent(BUILD / '.lock')
        final = flags()
        required = {'config', 'bootstrap', 'bootstrap_cache.save', 'chroot_install-packages.install',
                    'chroot_install-packages.live', 'chroot_package-lists.live',
                    'chroot_includes_after_packages', 'chroot_hooks', 'chroot_hacks'}
        if not required.issubset(final) or final & RUNTIME:
            raise ValueError('Public completion flags missing or runtime flags remain')
        allowed = INITIAL | {Path(p).name for p in SOURCE_PINS if p.startswith('/usr/lib/live/build/chroot_')}
        allowed |= {'chroot_package-lists.live', 'chroot_install-packages.install', 'chroot_install-packages.live'}
        if final - allowed:
            raise ValueError('Unexpected stage outside reviewed public chroot sources')
        sources()
        configurations()
        if read(overlay, 4096) != OVERLAY:
            raise ValueError('Private options changed during public chroot')
        report['installed_manifest'] = installed_manifest(workspace)
        quiet()
        report.update(chroot_completed=True, completed_flags=sorted(final), final_quiescent=True,
                      runtime_flags_absent=True, outcome='public-chroot-completed')
    except Exception as error:
        try:
            report['partial_stage_flags'] = sorted(flags())
            report['partial_status_sha256'] = digest(read(ROOT / 'var/lib/dpkg/status', 32 * 1024 * 1024))
        except Exception as observe_error:
            report['partial_state_error'] = str(observe_error)[:1024]
        report.update(error=str(error)[:2048], outcome='failed-retained-partial-state', chroot_completed=False)
        raise
    finally:
        report['finished'] = time.time()
        report_write(report, workspace, publish=reports_ready)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise SystemExit('Offline package stage refused: ' + str(error))
