"""Persistent preparation only: models, prompts and answers are never cached."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone

from arktic_office.resources.paths import resource_path


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def identity(acquired, *, scanners, indexer_signature):
    from arktic_office.preparation import repository, evidence
    from arktic_office.adapters import scanners as adapter, source_scan
    sources = [Path(__file__)] + [Path(m.__file__) for m in (repository, evidence, adapter, source_scan)]
    executables = {name: shutil.which(name) for name in ('gitleaks', 'osv-scanner', 'semgrep')}
    installation = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None
                    for name, path in executables.items()}
    if executables['semgrep']:
        base = Path(executables['semgrep']).resolve().parent.parent
        installation['semgrep_metadata'] = [hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(base.glob('lib/python*/site-packages/semgrep-*.dist-info/METADATA'))]
    rules = list(resource_path().rglob('*.yml')) + list(resource_path().rglob('*.yaml')) + [resource_path('profiles', 'semgrep-rules.json')]
    return digest({'schema': 1, 'content_policy': 'original-unmasked-v1', 'repository': acquired['repository'], 'commit': acquired['commit'],
        'local_path': acquired.get('local_source', {}).get('source_path'),
        'files': [{k: f.get(k) for k in ('path', 'mode', 'git_blob', 'sha256', 'bytes')} for f in acquired['inventory']],
        'scanners_enabled': scanners, 'indexer': indexer_signature,
        'scanner_installation': installation,
        'implementation': [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources + sorted(rules)]})


class PreparationCache:
    def __init__(self, root):
        self.root = Path(root)
        if self.root.is_symlink():
            raise ValueError('La caché no puede ser un enlace.')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def load(self, key, artifacts=None):
        entry = self.root / key
        try:
            if entry.is_symlink():
                return None
            manifest_path, payload_path = entry / 'manifest.json', entry / 'payload.json'
            if manifest_path.is_symlink() or payload_path.is_symlink() or payload_path.stat().st_size > 128_000_000:
                return None
            manifest = json.loads(manifest_path.read_text())
            payload = json.loads(payload_path.read_text())
            if manifest['key'] != key or digest(payload) != manifest['payload_sha256']:
                return None
            from arktic_office.config.models import integer
            max_age = integer('AUDIT_VULNERABILITY_MAX_AGE_SECONDS', 86400, 60, 604800)
            external = any('osv' in s.get('name', '').lower() for s in payload.get('scanners', []))
            if external and (datetime.now(timezone.utc) - datetime.fromisoformat(manifest['prepared_at'])).total_seconds() > max_age:
                return None
            for relative, checksum in manifest['artifacts'].items():
                path = Path(relative)
                if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
                    return None
                source = entry / 'artifacts' / path
                if any(p.is_symlink() for p in (source, *source.parents)) or hashlib.sha256(source.read_bytes()).hexdigest() != checksum:
                    return None
            if artifacts:
                for relative in manifest['artifacts']:
                    destination = Path(artifacts) / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(entry / 'artifacts' / relative, destination)
            return payload, {'status': 'reused', 'key': key, 'prepared_at': manifest['prepared_at']}
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save(self, key, payload, artifacts=None):
        entry = self.root / key
        # A complete entry is immutable. Invalid entries remain for diagnosis.
        if entry.exists() or entry.is_symlink():
            import uuid
            entry.rename(self.root / ('.superseded-' + key + '-' + uuid.uuid4().hex))
        with tempfile.TemporaryDirectory(prefix='.building-', dir=self.root) as temp:
            folder = Path(temp)
            files = {}
            if artifacts and Path(artifacts).is_dir():
                for source in Path(artifacts).rglob('*'):
                    if source.is_file() and not source.is_symlink():
                        relative = source.relative_to(artifacts)
                        destination = folder / 'artifacts' / relative
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(source, destination)
                        files[relative.as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
            (folder / 'payload.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            (folder / 'manifest.json').write_text(json.dumps({'key': key, 'payload_sha256': digest(payload),
                'prepared_at': datetime.now(timezone.utc).isoformat(), 'artifacts': files}), encoding='utf-8')
            os.rename(folder, entry)
            # TemporaryDirectory tolerates the renamed directory on cleanup.
