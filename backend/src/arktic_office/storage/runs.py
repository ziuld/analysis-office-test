"""Resolve stable run IDs independently of their physical folder layout."""
from pathlib import Path
from datetime import datetime, timezone
from arktic_office.storage.jsonio import read_json
from arktic_office.core.contracts import ACTIVE_STATES
import re
from functools import lru_cache

from arktic_office.core.errors import AuditError

SAFE_ID = re.compile(r"[a-zA-Z0-9_-]{8,80}\Z")
MARKERS = ("job.json", "evidencia.json", "informe.json")


@lru_cache(maxsize=256)
def cached_json(path, stamp, size):
    return read_json(Path(path), {})


def immutable_json(path):
    try:
        stat = path.stat()
        return cached_json(str(path), stat.st_mtime_ns, stat.st_size)
    except OSError:
        return {}


class RunStore:
    def __init__(self, root, *, max_depth=4, max_directories=10000):
        self.root = Path(root)
        self.max_depth = max_depth
        self.max_directories = max_directories

    @staticmethod
    def validate_id(run_id):
        if not isinstance(run_id, str) or not SAFE_ID.fullmatch(run_id):
            raise AuditError("Identificador de revisión inválido.")

    def directories(self):
        """Bounded discovery, never follow links or descend into run contents."""
        base = self.root.resolve()
        pending = [(self.root, 0)]
        seen = 0
        found = {}
        while pending:
            parent, depth = pending.pop()
            if not parent.is_dir():
                continue
            for path in sorted(parent.iterdir(), key=lambda p: p.name, reverse=True):
                if path.name.startswith(".") or path.is_symlink() or not path.is_dir():
                    continue
                seen += 1
                if seen > self.max_directories:
                    raise AuditError("Demasiadas carpetas de resultados; revisar el almacenamiento.")
                if not path.resolve().is_relative_to(base):
                    continue
                if SAFE_ID.fullmatch(path.name) and any((path / marker).is_file() for marker in MARKERS):
                    if path.name in found:
                        raise AuditError("Identificador de revisión duplicado; no se eligió un informe arbitrario.")
                    found[path.name] = path
                elif depth + 1 < self.max_depth:
                    pending.append((path, depth + 1))
        return list(found.values())

    def resolve(self, run_id):
        self.validate_id(run_id)
        matches = [path for path in self.directories() if path.name == run_id]
        if not matches:
            raise FileNotFoundError()
        return matches[0]

    def create(self, run_id, *, exist_ok=False, repository=None):
        self.validate_id(run_id)
        try:
            path = self.resolve(run_id)
        except FileNotFoundError:
            path = self.root / run_id
            if repository:
                now = datetime.now(timezone.utc)
                title = re.sub(r"[^a-zA-Z0-9_-]+", "-", repository.rstrip('/').split('/')[-1])[:60] or "revision"
                path = self.root / now.strftime("%Y-%m-%d") / (now.strftime("%H%M%S") + "-" + title) / run_id
            # An unmarked folder or link is not safe to reuse as a new result.
            if not path.resolve().is_relative_to(self.root.resolve()):
                raise AuditError("La carpeta de resultados sale del directorio configurado.")
            for parent in (path, *path.parents):
                if parent == self.root:
                    break
                if parent.is_symlink():
                    raise AuditError("No se reutilizan enlaces en carpetas de resultados.")
            if path.exists() or path.is_symlink():
                raise FileExistsError(path)
            path.mkdir(parents=True)
            return path
        if not exist_ok:
            raise FileExistsError(path)
        return path

    def detail(self, run_id):
        return self.record(self.resolve(run_id))

    def record(self, path, *, brief=False):
        job_id = path.name
        job = read_json(path / "job.json")
        # Polling must not parse all captured source text every two seconds.
        manifest = immutable_json(path / 'manifest.json') if brief else {}
        snapshot = manifest or immutable_json(path / "evidencia.json")
        compatibility_fields = {'simulation', 'source_revision', 'evidence_origin'}
        if manifest and not compatibility_fields <= set(manifest):
            original = immutable_json(path / 'evidencia.json')
            snapshot = {**manifest, **{k: original.get(k) for k in compatibility_fields}}
        team = read_json(path / "estado.json", {})
        report = immutable_json(path / "informe.json")
        if job is None:
            if not snapshot or not report:
                raise FileNotFoundError()
            job = {"id": job_id, "repository": snapshot["repository"], "estado": report.get("estado", "completo"),
                   "historical": True, "created": datetime.fromtimestamp((path / "informe.md").stat().st_mtime, timezone.utc).isoformat()}
        if job["estado"] in ACTIVE_STATES and not snapshot:
            job = {**job, "estado": "preparando"}
        cells = team.get("celulas", report.get("celulas", []))
        coordination = read_json(path / 'coordinacion.json', {})
        from arktic_office.execution.activity import project
        return {**job, "commit": snapshot.get("commit",job.get('commit')), "branch": snapshot.get("branch",job.get('branch')), "celulas": cells,
                "meeting": read_json(path / 'meeting.json', {}) if job['estado'] in ACTIVE_STATES else {'active': False},
                "metrics": read_json(path / 'metrics.json', {}),
                "coordination": coordination,
                "activity": project(path, job, cells),
                "mensaje": report.get("mensaje"), "necesita": report.get("necesita", []),
                "has_report": (path / "informe.md").is_file(), "has_html_report": (path / "informe.html").is_file(), "evidence_origin": snapshot.get("evidence_origin"),
                "report_format": report.get("schema_version", 1), "derived_from": snapshot.get("source_revision"), "simulation": bool(snapshot.get("simulation", report.get('simulation', False)))}

    def listing(self):
        items = []
        for path in self.directories():
            try:
                items.append(self.record(path, brief=True))
            except (FileNotFoundError, KeyError):
                continue
        return sorted(items, key=lambda x: x.get("created", ""), reverse=True)[:30]
