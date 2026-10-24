#!/usr/bin/env python3
"""Create a deterministic desktop-overlay .deb; run only in the contained VM.
No installation or host mutation. All outputs are under this project's artifacts/.
"""
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0~preview1'
CONTROL = f'''Package: windows12-desktop
Version: {VERSION}
Architecture: all
Maintainer: Windows12 project <64068873+avision1@users.noreply.github.com>
Section: x11
Priority: optional
Depends: python3, xdg-utils, plasma-desktop, dolphin, plasma-discover, chromium | firefox-esr
Description: Independent Windows-style Linux desktop integration preview
 Curated Office web launchers, offline help, initial Plasma defaults,
 and original wallpaper. This package is independent of Microsoft.
 It does not provide native Microsoft Office or Windows binary parity.
'''


def tarball(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, data, mode in sorted(entries):
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = mode
            entry.uid = entry.gid = 0
            entry.uname = entry.gname = 'root'
            entry.mtime = 0
            archive.addfile(entry, io.BytesIO(data))
    return gzip.compress(output.getvalue(), mtime=0)


def member(name, data):
    header = f'{name + "/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'
    return header.encode('ascii') + data + (b'\n' if len(data) % 2 else b'')


def main():
    # Package only project files. Refuse symlink input/output escape paths.
    if not Path('/run/windows12-build-vm').is_file():
        raise SystemExit('Run packaging inside the contained Windows12 build VM')
    image = ROOT / 'image'
    entries = []
    for path in sorted(image.rglob('*')):
        if path.is_symlink():
            raise SystemExit('Overlay symlinks require explicit review: ' + str(path))
        if path.is_file():
            if not path.resolve().is_relative_to(image.resolve()):
                raise SystemExit('Input escapes image/')
            entries.append(('./' + path.relative_to(image).as_posix(), path.read_bytes(), 0o755 if path.stat().st_mode & 0o111 else 0o644))
    if not entries:
        raise SystemExit('Empty desktop overlay')
    out = ROOT / 'artifacts/packages'
    if not out.resolve().is_relative_to(ROOT):
        raise SystemExit('Output escapes project')
    out.mkdir(parents=True, exist_ok=True)
    package = out / f'windows12-desktop_{VERSION}_all.deb'
    if package.is_symlink():
        raise SystemExit('Output symlink refused')
    payload = b'!<arch>\n' + member('debian-binary', b'2.0\n') + member('control.tar.gz', tarball([('./control', CONTROL.encode(), 0o644), ('./conffiles', b'/etc/skel/.config/kdeglobals\n/etc/skel/.config/kwinrc\n', 0o644)])) + member('data.tar.gz', tarball(entries))
    package.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    checksum = out / 'SHA256SUMS'
    if checksum.is_symlink():
        raise SystemExit('Checksum symlink refused')
    checksum.write_text(f'{digest}  {package.name}\n')
    print(package)
    print(digest)


if __name__ == '__main__':
    main()
