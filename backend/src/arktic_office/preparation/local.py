"""Verify an explicitly supplied local Git bundle; never read arbitrary host paths."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time
from arktic_office.config.models import integer
from arktic_office.core.errors import AuditError


def acquire_local(bundle, workspace):
    started = time.monotonic()
    maximum = integer('AUDIT_SNAPSHOT_MAX_BYTES',32_000_000,1_000_000,256_000_000)
    maximum_files = integer('AUDIT_SNAPSHOT_MAX_FILES',20000,1,100000)
    seconds = integer('AUDIT_SNAPSHOT_SECONDS',300,1,1800)
    try:
        bundle = Path(bundle).resolve(strict=True)
        manifest_path = bundle/'snapshot.json'
        if manifest_path.is_symlink() or manifest_path.stat().st_size > 8_000_000:
            raise ValueError()
        meta = json.loads(manifest_path.read_text(encoding='utf-8'))
        if (meta.get('schema_version') != 1 or meta.get('source_type') != 'local_git'
            or meta.get('dirty') is not False or meta.get('scope') != 'tracked_HEAD'
            or not isinstance(meta.get('repository'),str) or not meta['repository'].startswith('local:///')
            or not isinstance(meta.get('branch'),str) or not meta['branch'] or len(meta['branch']) > 255
            or not re.fullmatch(r'[0-9a-f]{40}',meta.get('commit',''))
            or not isinstance(meta.get('files'),list) or not 0 < len(meta['files']) <= maximum_files):
            raise ValueError()
        root = bundle/'source'
        if root.is_symlink(): raise ValueError()
        source = Path(workspace)/'source'
        source.mkdir()
        records, inventory, seen, total = [], [], set(), 0
        for item in meta['files']:
            path = item['path']
            parts = PurePosixPath(path).parts
            if (not parts or PurePosixPath(path).as_posix() != path or path.startswith('/') or any(p in {'.','..','.git'} for p in parts)
                or '\\' in path or ':' in path or path in seen or len(path) > 500
                or item.get('mode') not in {'100644','100755','120000'}
                or type(item.get('bytes')) is not int or item['bytes'] < 0):
                raise ValueError()
            original = root.joinpath(*parts)
            if any(p.is_symlink() for p in [original,*original.parents] if p != bundle.parent):
                raise ValueError()
            if not original.resolve(strict=True).is_relative_to(root) or original.stat().st_size != item['bytes']:
                raise ValueError()
            total += item['bytes']
            if total > maximum or time.monotonic()-started > seconds: raise ValueError()
            raw = original.read_bytes()
            blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if blob != item['git_blob'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError()
            if raw.splitlines()[:1] == [b'version https://git-lfs.github.com/spec/v1']: raise ValueError()
            target = source.joinpath(*parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            try: text = raw.decode('utf-8') if b'\0' not in raw else None
            except UnicodeError: text = None
            kind = 'symlink_metadata' if item['mode']=='120000' else 'text' if text is not None else 'binary'
            records.append({'path':path,'text':text,'kind':kind})
            inventory.append({**item,'kind':kind,'retrieval':'local_git_blob'})
            seen.add(path)
        if total != meta.get('bytes'): raise ValueError()
        return {'repository':meta['repository'],'project_name':meta.get('project_name'),
                'branch':meta['branch'],'commit':meta['commit'],'source_type':'local_git',
                'local_source':{k:meta.get(k) for k in ('source_path','scope','dirty','detached_head')},
                'files':records,'inventory':inventory,'excluded':[],'tree_files':len(records),
                'bytes_downloaded':total,'acquisition_complete':True,
                'acquisition_seconds':round(time.monotonic()-started,3),
                'acquisition_limits':{'bytes':maximum,'files':maximum_files,'seconds':seconds}}
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        raise AuditError('Snapshot local incompleto o inválido; no se inicia el análisis. Volver a capturar la rama activa.') from exc
