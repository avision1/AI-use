#!/usr/bin/env python3
"""Emit reviewed staged project text files for GitHub create_tree.
Run git diff --cached first. This does not publish or modify the repository.
"""
import json
from pathlib import Path
import subprocess
import sys

project = Path(__file__).resolve().parent.parent
repo = project.parent
if project.name != 'windows12' or not (repo / '.git').is_dir():
    raise SystemExit('Expected sole AI-use/windows12 checkout')

def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])

names = git('diff', '--cached', '--name-only', '-z').decode().split('\0')
names = [n for n in names if n]
if not names:
    raise SystemExit('Nothing staged')
if any(not n.startswith('windows12/') or '..' in Path(n).parts for n in names):
    raise SystemExit('Refusing staged changes outside windows12/')
entries = []
for name in names:
    record = git('ls-files', '--stage', '--', name).decode().strip()
    if not record:
        entries.append({'path': name, 'mode': '100644', 'type': 'blob', 'sha': None})
        continue
    mode, sha, stage_path = record.split(maxsplit=2)
    if mode not in ('100644', '100755'):
        raise SystemExit('Refusing symlink/submodule/conflict: ' + name)
    content = git('show', ':' + name)
    if len(content) > 1024 * 1024 or b'\0' in content:
        raise SystemExit('Refusing binary/large staged content: ' + name)
    entries.append({'path': name, 'mode': mode, 'type': 'blob', 'content': content.decode('utf-8')})
json.dump(entries, sys.stdout)
print()
