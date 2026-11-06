"""Explicit local verifier for your own patched Binary School training executable."""
import argparse
import pathlib
import subprocess

VARIANTS = {'cedar': (3, 4, 5, 'north'), 'quartz': (2, 6, 7, 'delta'), 'willow': (4, 3, 8, 'cabin')}

def expected(name, n, adjustment=9):
    threshold, rate, bonus, _ = VARIANTS[name]
    return sum(rate if i < threshold else rate+2 for i in range(n)) - (bonus if n > threshold else 0) + adjustment

def check(name, executable):
    executable = str(pathlib.Path(executable).resolve())
    token = VARIANTS[name][3]
    cases = [([str(n), token, '0'], 0, 'charge={}\n'.format(expected(name,n))) for n in range(9)]
    cases += [(['3','wrong','0'],3,None),(['3',token,'1'],3,None),(['-1',token,'0'],2,None),(['9',token,'0'],2,None),(['oops',token,'0'],2,None),(['3',token,'x'],2,None),([],2,None)]
    for args, code, suffix in cases:
        result = subprocess.run([executable]+args, capture_output=True, text=True, timeout=3)
        if result.returncode != code or (suffix is not None and not result.stdout.endswith(suffix)):
            raise AssertionError('Mismatch: {} => exit {}, stdout {!r}; expected exit {}, suffix {!r}'.format(args,result.returncode,result.stdout,code,suffix))
    return len(cases)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__+' This runs the executable locally; the website never executes uploads.')
    parser.add_argument('variant',choices=VARIANTS)
    parser.add_argument('executable',help='path to your own patched training binary, for the current OS/architecture')
    args = parser.parse_args()
    print('Passed {} behavior cases. Self-review the evidence and reconstructed C too.'.format(check(args.variant,args.executable)))
