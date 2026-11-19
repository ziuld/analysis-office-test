"""Local state, source identity and atomic publication for portable Iris."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import site
import subprocess
import tempfile

KIT = Path(__file__).resolve().parents[1]
LOCAL = KIT / ".local"
SKIP = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", ".next",
        "dist", "build", ".local", "coverage", "graphify-out", ".turbo"}
PRIVATE = {".pem", ".key", ".pfx", ".p12", ".sqlite", ".db"}
SENSITIVE = re.compile(r"""(?im)(\b(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|secret|token)\b\s*['"]?\s*[:=]\s*)(['"])([^\r\n]*?)\2""")
TOKEN = re.compile(r"\b(?:gh[pousr]_|github_pat_|sk-(?:proj-)?|xox[baprs]-)[A-Za-z0-9_-]{16,}\b")


def protect(text):
    text = SENSITIVE.sub(lambda m: m[1] + m[2] + "<valor protegido>" + m[2], text)
    text = TOKEN.sub("<valor protegido>", text)
    text = re.sub(r"(?i)([a-z][a-z0-9+.-]*://[^\s:/@]+:)[^\s/@]+@", r"\1<valor protegido>@", text)
    return text


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def file_hash(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def require_project(root):
    root = Path(root).resolve(strict=True)
    if root == KIT or not KIT.is_relative_to(root):
        raise ValueError(f'Iris debe ejecutarse desde su carpeta instalada dentro del proyecto {root}. '
                         'No copies el agente a outputs ni a otro workspace para eludir permisos.')
    return root


def local_path(path):
    path = Path(path).absolute()
    if not path.is_relative_to(LOCAL) or not path.resolve().is_relative_to(LOCAL.resolve()):
        raise ValueError('El destino debe estar dentro de la .local del agente instalado en el proyecto.')
    if LOCAL.is_symlink() or any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(LOCAL)):
        raise ValueError('El almacenamiento no admite enlaces a otros destinos.')
    return path


def atomic_text(path, value):
    path = local_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.iris-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf8', newline='\n') as stream:
            stream.write(value)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, value):
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2))


def environment(home):
    home.mkdir(parents=True, exist_ok=True)
    names = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "HTTPS_PROXY", "HTTP_PROXY",
             "NO_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE")
    env = {key: os.environ[key] for key in names if key in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), TMP=str(home), TEMP=str(home), TMPDIR=str(home),
               APPDATA=str(home / "appdata"), LOCALAPPDATA=str(home / "appdata-local"),
               PYTHONUSERBASE=site.getuserbase(),
               XDG_CACHE_HOME=str(home / "cache"), XDG_CONFIG_HOME=str(home / "config"),
               PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", GRAPHIFY_BACKEND="none",
               GRAPHIFY_QUERY_LOG_DISABLE="1", GRAPHIFY_NO_TIPS="1", SEMGREP_SEND_METRICS="off",
               GOMAXPROCS="2",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_OPTIONAL_LOCKS="0",
               GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="")
    return env


@contextmanager
def locked():
    if LOCAL.is_symlink() or not LOCAL.resolve().is_relative_to(KIT.resolve()):
        raise ValueError(".local debe ser una carpeta propia dentro del paquete de Iris.")
    try:
        LOCAL.mkdir(parents=True, exist_ok=True)
        path = local_path(LOCAL / 'iris.lock')
        lock = path.open('a+b')
    except PermissionError as exc:
        raise PermissionError(f'Falta permiso para crear o usar {LOCAL}. Solicita acceso de escritura y '
                              'reintenta en esa misma ruta; no existe destino alternativo.') from exc
    with lock as stream:
        stream.seek(0)
        stream.write(b"0")
        stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError("Ya hay una operación de Iris activa en esta carpeta.") from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def git(root, *args):
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_OPTIONAL_LOCKS="0",
               GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="")
    try:
        result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                                 "-C", str(root), *args], env=env, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def profile_hash():
    files = {}
    for directory, folders, names in os.walk(KIT, followlinks=False):
        folders[:] = [name for name in folders if name not in {".local", "__pycache__"}
                      and not (Path(directory) / name).is_symlink()]
        for name in sorted(names):
            path = Path(directory) / name
            if not path.is_symlink() and path.suffix != ".pyc":
                files[path.relative_to(KIT).as_posix()] = file_hash(path)
    return digest(files)


def inventory(root, exclusions=()):
    root = require_project(root)
    excluded = sorted({Path(name).as_posix() for name in exclusions})
    if any(Path(name).is_absolute() or Path(name).drive or '..' in Path(name).parts or name == '.' for name in excluded):
        raise ValueError("Las exclusiones deben ser rutas relativas dentro del proyecto, sin '..'.")
    if root == KIT or root.is_relative_to(KIT):
        raise ValueError("El proyecto debe estar fuera de la carpeta de Iris.")
    top = git(root, "rev-parse", "--show-toplevel")
    if top and Path(os.fsdecode(top).strip()).resolve() != root:
        raise ValueError("Indica la raíz Git del proyecto.")
    listed = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard") if top else None
    if top and listed is None:
        raise ValueError("No se pudo inventariar el Git del proyecto.")
    if listed is not None:
        candidates = sorted({os.fsdecode(name) for name in listed.split(b"\0") if name})
    else:
        candidates = []
        for directory, folders, files in os.walk(root, followlinks=False):
            folders[:] = [name for name in folders if name not in SKIP
                          and not (Path(directory) / name).is_symlink()
                          and (Path(directory) / name).resolve() != KIT]
            candidates.extend((Path(directory) / name).relative_to(root).as_posix() for name in files)
        candidates.sort()
    records = []
    exported = read_json(LOCAL / "exports.json", [])
    for name in candidates:
        path = root / name
        if str(path.resolve()) in exported:
            continue
        if not path.exists() and not path.is_symlink():
            continue
        relative = path.relative_to(root)
        if path.is_relative_to(KIT) or any(part in SKIP for part in relative.parts):
            continue
        if any((root.joinpath(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            records.append({"path": relative.as_posix(), "kind": "excluded_link",
                            "sha256": digest(os.readlink(path)) if path.is_symlink() else "linked_parent"})
            continue
        if not path.is_file():
            continue
        if any(relative.is_relative_to(Path(name)) for name in excluded):
            records.append({"path": relative.as_posix(), "kind": "excluded_scope", "sha256": "excluded_by_scope"})
            continue
        size = path.stat().st_size
        kind = "text"
        if path.suffix.lower() in PRIVATE:
            kind = "excluded_private"
        elif size > 2_000_000:
            kind = "excluded_size"
        else:
            raw = path.read_bytes()
            try:
                raw.decode("utf-8")
                if b"\0" in raw:
                    kind = "excluded_binary"
            except UnicodeError:
                kind = "excluded_binary"
        records.append({"path": relative.as_posix(), "bytes": size, "sha256": file_hash(path), "kind": kind})
    revision = git(root, "rev-parse", "HEAD") if top else None
    branch = git(root, "symbolic-ref", "--short", "-q", "HEAD") if top else None
    identity = digest({"root": str(root), "files": records, "exclusions": excluded})
    return {"root": str(root), "identity": identity, "files": records,
            "exclusions": excluded,
            "commit": revision.decode().strip() if revision else None,
            "branch": branch.decode().strip() if branch else None, "scope": "working_tree",
            "profile": profile_hash()}


def intact(folder, state):
    artifacts = state.get("artifacts") if isinstance(state, dict) else None
    if not artifacts:
        return False
    return all((folder / name).is_file() and file_hash(folder / name) == fingerprint
               for name, fingerprint in artifacts.items())


def artifacts(folder):
    return {p.relative_to(folder).as_posix(): file_hash(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and p.name != "estado.json" and "__pycache__" not in p.parts}
