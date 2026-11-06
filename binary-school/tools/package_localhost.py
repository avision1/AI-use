"""Build a verified, reproducible student ZIP using only Python's standard library."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = {'README.md', 'README.txt', 'CHANGELOG.txt', 'VERIFICATION.md',
             'start.py', 'start.sh', 'Start-Windows.bat', 'Start-macOS.command'}


def build(output):
    output = Path(output).resolve()
    if output.suffix.lower() != '.zip':
        raise ValueError('The package output must have a .zip extension')
    if ROOT not in output.parents:
        raise ValueError('Write the package inside binary-school/, for example .qa/BinarySchool-Localhost.zip')
    manifest = json.loads((ROOT / 'SHA256SUMS.json').read_text(encoding='utf-8'))
    payload = {}
    for name, expected in sorted(manifest.items()):
        relative = Path(name)
        if relative.is_absolute() or any(p in ('.', '..') for p in relative.parts):
            raise ValueError('Invalid manifest path: ' + name)
        if name not in TOP_LEVEL and relative.parts[0] not in ('site', 'docs'):
            continue
        source = (ROOT / relative).resolve()
        if ROOT not in source.parents or source == output:
            raise ValueError('Invalid package source: ' + name)
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Checksum mismatch; refresh the manifest after reviewing changes: ' + name)
        payload[name] = data
    if not TOP_LEVEL.issubset(payload) or 'site/index.html' not in payload:
        raise ValueError('The integrity manifest is missing required startup files')
    checksums = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())}
    payload['SHA256SUMS.json'] = (json.dumps(checksums, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + '.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(payload.items()):
                info = zipfile.ZipInfo('BinarySchool-Localhost/' + name, (2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                executable = name in ('start.sh', 'Start-macOS.command') or data.startswith(b'\x7fELF')
                info.external_attr = (0o100755 if executable else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.qa/BinarySchool-Localhost.zip')
    args = parser.parse_args()
    try:
        result = build(args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(result)
    print('SHA256: ' + hashlib.sha256(result.read_bytes()).hexdigest())
