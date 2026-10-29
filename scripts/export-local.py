"""Export active Git HEAD through object reads; never checkout or execute target code."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from urllib.parse import quote, unquote


def export(repository, destination, origin=None, autocrlf=None, filemode=None):
    repository = Path(repository).resolve()
    command = ['git', '-c', f'safe.directory={repository}', '-c', 'core.fsmonitor=false',
               '--no-optional-locks', '-C', str(repository)]
    for key,value in [('autocrlf',autocrlf),('filemode',filemode)]:
        if value is not None:
            if value not in ({'true','false','input'} if key=='autocrlf' else {'true','false'}):
                raise ValueError('Configuración Git local no válida.')
            command[1:1] = ['-c',f'core.{key}={value}']
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0', 'GIT_CONFIG_NOSYSTEM': '1'}
    def git(*args):
        return subprocess.check_output(command + list(args), env=env, stderr=subprocess.PIPE, timeout=60)
    top = Path(os.fsdecode(git('rev-parse', '--show-toplevel').strip())).resolve()
    if top != repository:
        raise ValueError('La ruta debe ser la raíz del repositorio Git.')
    commit = git('rev-parse', 'HEAD').decode().strip()
    branch = git('rev-parse', '--abbrev-ref', 'HEAD').decode().strip()
    filters = subprocess.run(command+['config','--name-only','--get-regexp',r'^filter\..*\.(clean|smudge|process)$'],
                             env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
    if filters.returncode == 0:
        raise ValueError('Filtros Git personalizados no admitidos: podrían ejecutar código durante la comprobación de cambios.')
    if filters.returncode != 1: raise ValueError('No se pudo verificar la configuración de filtros Git.')
    if git('status', '--porcelain=v1', '--untracked-files=normal').strip():
        raise ValueError('Hay cambios locales o archivos sin seguimiento. Esta modalidad analiza HEAD; confirma los cambios antes de continuar.')
    entries = []
    for entry in git('ls-tree', '-r', '-z', 'HEAD').split(b'\0'):
        if not entry: continue
        meta, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        path = raw_path.decode('utf-8')
        parts = PurePosixPath(path).parts
        if kind != 'blob' or mode not in {'100644', '100755', '120000'}:
            raise ValueError('Submódulo/tipo de archivo no compatible; no se omite silenciosamente.')
        if not parts or path.startswith('/') or any(x in {'.', '..', '.git'} for x in parts) or '\\' in path or ':' in path:
            raise ValueError('Ruta de archivo no compatible.')
        entries.append((path, mode, oid))
    if not entries or len(entries) > 20000:
        raise ValueError('Snapshot vacío o fuera del límite de 20000 archivos.')
    destination = Path(destination)
    source = destination / 'source'
    source.mkdir(parents=True, exist_ok=False)
    files, total = [], 0
    # Each request returns canonical bytes; export-ignore and CRLF filters cannot remove/change files.
    with subprocess.Popen(command + ['cat-file', '--batch'], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) as process:
        try:
            for path, mode, oid in entries:
                process.stdin.write((oid+'\n').encode()); process.stdin.flush()
                actual_oid, kind, size = process.stdout.readline().decode().strip().split()
                size = int(size)
                if actual_oid != oid or kind != 'blob' or total + size > 32_000_000:
                    raise ValueError('Objeto inválido o snapshot superior a 32 MB.')
                raw = process.stdout.read(size)
                if process.stdout.read(1) != b'\n' or len(raw) != size:
                    raise ValueError('Objeto Git incompleto.')
                if hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest() != oid:
                    raise ValueError('Objeto Git no verificado.')
                if raw.splitlines()[:1] == [b'version https://git-lfs.github.com/spec/v1']:
                    raise ValueError('Puntero LFS sin contenido; no se analiza una muestra incompleta.')
                target = source / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                files.append({'path':path, 'mode':mode, 'git_blob':oid,
                              'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':size})
                total += size
            process.stdin.close()
            if process.wait(timeout=10): raise ValueError('No se completó la lectura de objetos.')
        finally:
            if process.poll() is None: process.kill(); process.wait()
    if git('rev-parse', 'HEAD').decode().strip() != commit or git('rev-parse', '--abbrev-ref', 'HEAD').decode().strip() != branch or git('status', '--porcelain=v1', '--untracked-files=normal').strip():
        raise ValueError('El repositorio cambió durante la captura; repetir antes de analizar.')
    label = (PureWindowsPath(origin).name if '\\' in origin else Path(origin).name) if origin else repository.name
    manifest = {'schema_version':1, 'source_type':'local_git', 'repository':'local:///'+quote(label, safe=''),
                'project_name':unquote(label), 'source_path':origin or str(repository), 'branch':branch,
                'detached_head':branch == 'HEAD', 'commit':commit, 'dirty':False,
                'scope':'tracked_HEAD', 'files':files, 'bytes':total}
    (destination/'snapshot.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'branch':branch,'commit':commit,'files':len(files),'bytes':total},ensure_ascii=False), flush=True)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository'); parser.add_argument('destination'); parser.add_argument('--origin')
    parser.add_argument('--autocrlf',choices=['true','false','input'])
    parser.add_argument('--filemode',choices=['true','false'])
    args = parser.parse_args()
    try: export(args.repository,args.destination,args.origin,args.autocrlf,args.filemode)
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        raise SystemExit('No se pudo capturar el repositorio local: '+str(exc))
