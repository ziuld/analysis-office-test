"""Only explicitly prepared bundles are exposed to the web API; never arbitrary host paths."""
import json
import os
from pathlib import Path
import re
import uuid
from arktic_office.core.errors import AuditError


def local_source(source_id):
    try:
        if not isinstance(source_id,str) or str(uuid.UUID(source_id)) != source_id: raise ValueError()
        configured = os.environ.get('AUDIT_LOCAL_INPUTS_ROOT')
        if not configured: raise ValueError()
        root = Path(configured).resolve(strict=True)
        folder = root/source_id
        if folder.is_symlink() or not folder.resolve(strict=True).is_relative_to(root): raise ValueError()
        manifest = folder/'snapshot.json'
        if manifest.is_symlink() or manifest.stat().st_size > 8_000_000: raise ValueError()
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if (data.get('schema_version') != 1 or data.get('source_type') != 'local_git'
            or data.get('dirty') is not False or data.get('scope') != 'tracked_HEAD'
            or not isinstance(data.get('repository'),str) or not data['repository'].startswith('local:///')
            or not isinstance(data.get('branch'),str) or not 0 < len(data['branch']) <= 255
            or not re.fullmatch(r'[0-9a-f]{40}',data.get('commit',''))): raise ValueError()
        return {'id':source_id,'name':str(data.get('project_name') or data['repository'])[:250],
                'repository':data['repository'],'branch':data['branch'],'commit':data['commit'],
                'source_path':str(data.get('source_path',''))[:1000], 'folder':folder}
    except (OSError,ValueError,TypeError,AttributeError) as exc:
        raise AuditError('Repositorio local no disponible. Preparar su captura en este equipo antes de iniciar.') from exc


def local_sources():
    configured = os.environ.get('AUDIT_LOCAL_INPUTS_ROOT')
    if not configured or not Path(configured).is_dir(): return []
    result=[]
    from itertools import islice
    for folder in islice(Path(configured).iterdir(),1001):
        if len(result) >= 100: break
        try: item=local_source(folder.name)
        except AuditError: continue
        result.append({k:v for k,v in item.items() if k != 'folder'})
    return sorted(result,key=lambda x:(x['name'],x['id']))
