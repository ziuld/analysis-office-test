"""Synchronize distributable copies of the neutral Iris core and template; default is check-only."""
import argparse
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ('backend/src/arktic_office/reporting/iris_core.py','full-stack-code-analyst/scripts/iris_core.py'),
    ('backend/src/arktic_office/resources/assets/iris-template.html','full-stack-code-analyst/plantillas/informe.html'),
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Update distributable copies from the canonical source')
    args = parser.parse_args()
    for source_name,target_name in PAIRS:
        source,target = ROOT / source_name,ROOT / target_name
        if args.write:
            shutil.copyfile(source,target)
        if source.read_bytes() != target.read_bytes():
            raise SystemExit(f'Divergencia de contrato: {target_name}. Ejecuta --write tras revisar el cambio canónico.')
        print(target_name + ' · sha256 ' + hashlib.sha256(target.read_bytes()).hexdigest())

if __name__ == '__main__':
    main()
