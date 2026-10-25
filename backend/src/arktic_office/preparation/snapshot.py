"""Complete immutable GitHub snapshot. Operational limits fail closed, never sample."""
import base64
import hashlib
import os
import tarfile
import time
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, build_opener

from arktic_office.config.models import integer
from arktic_office.preparation.repository import AuditError, github, parse_repo, NoRedirect


def download(owner, repo, commit, destination, limit, seconds):
    headers = {"User-Agent": "Arktic-Office"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    request = Request(f"https://codeload.github.com/{owner}/{repo}/tar.gz/{commit}", headers=headers)
    started, size = time.monotonic(), 0
    with build_opener(NoRedirect()).open(request, timeout=30) as response, destination.open("xb") as output:
        while chunk := response.read(65536):
            size += len(chunk)
            if size > limit or time.monotonic() - started > seconds:
                raise AuditError("Snapshot incompleto: límite de descarga; no se analizará un subconjunto.")
            output.write(chunk)


def acquire_complete(url, workspace, *, fetch=github, downloader=download):
    started = time.monotonic()
    owner, repo = parse_repo(url)
    root = f"/repos/{owner}/{repo}"
    branch = fetch(root)["default_branch"]
    commit = fetch(root + "/branches/" + quote(branch, safe=""))["commit"]
    tree = fetch(root + "/git/trees/" + commit["commit"]["tree"]["sha"] + "?recursive=1")
    if tree.get("truncated"):
        raise AuditError("Snapshot incompleto: GitHub truncó el árbol; no se inicia el análisis.")
    expected = {x["path"]: x for x in tree["tree"] if x["type"] in {"blob", "commit"}}
    maximum = integer("AUDIT_SNAPSHOT_MAX_BYTES", 32_000_000, 1_000_000, 256_000_000)
    maximum_files = integer("AUDIT_SNAPSHOT_MAX_FILES", 20000, 1, 100000)
    seconds = integer("AUDIT_SNAPSHOT_SECONDS", 300, 1, 1800)
    if len(expected) > maximum_files or sum(x.get("size", 0) for x in expected.values()) > maximum:
        raise AuditError("Snapshot incompleto: capacidad insuficiente; no se descarga una muestra.")
    if any(x["type"] == "commit" for x in expected.values()):
        raise AuditError("Snapshot incompleto: submódulos requieren recuperar sus commits; no se omiten silenciosamente.")
    workspace = Path(workspace)
    source = workspace / "source"
    source.mkdir()
    archive = workspace / "snapshot.tar.gz"
    try:
        downloader(owner, repo, commit["sha"], archive, maximum, seconds)
        records, inventory, seen, total = [], [], set(), 0
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                if time.monotonic() - started > seconds:
                    raise AuditError("Snapshot incompleto: tiempo de adquisición agotado.")
                parts = PurePosixPath(member.name).parts
                if not parts or member.name.startswith("/") or ".." in parts or "\\" in member.name:
                    raise AuditError("Ruta insegura en el snapshot.")
                if member.isdir():
                    continue
                path = PurePosixPath(*parts[1:]).as_posix()
                if path not in expected or path in seen or ":" in path or ".git" in PurePosixPath(path).parts:
                    raise AuditError("Snapshot incompleto: archivo inesperado o duplicado.")
                item = expected[path]
                if member.issym() and item.get("mode") == "120000":
                    raw = member.linkname.encode()
                    total += len(raw)
                    if total > maximum:
                        raise AuditError("Snapshot incompleto: expansión supera capacidad.")
                    kind = "symlink_metadata"
                elif member.isfile() and item.get("mode") != "120000":
                    total += member.size
                    if total > maximum:
                        raise AuditError("Snapshot incompleto: expansión supera capacidad.")
                    with tar.extractfile(member) as stream:
                        raw = stream.read(member.size + 1)
                    kind = "text"
                else:
                    raise AuditError("Snapshot incompleto: tipo de archivo no recuperable.")
                blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                retrieval = "archive"
                if blob != item["sha"]:
                    # Git archives can apply .gitattributes (e.g. eol=crlf).
                    # Recover canonical bytes by immutable blob ID, never waive the hash check.
                    original = fetch(root + "/git/blobs/" + item["sha"])
                    if original.get("encoding") != "base64" or not isinstance(original.get("content"), str):
                        raise AuditError("Snapshot incompleto: blob original no recuperable.")
                    canonical = base64.b64decode("".join(original["content"].split()), validate=True)
                    canonical_hash = hashlib.sha1(b"blob " + str(len(canonical)).encode() + b"\0" + canonical).hexdigest()
                    if canonical_hash != item["sha"]:
                        raise AuditError("Snapshot incompleto: contenido no coincide con el commit.")
                    total += len(canonical) - len(raw)
                    if total > maximum or time.monotonic() - started > seconds:
                        raise AuditError("Snapshot incompleto: recuperar blob supera capacidad o tiempo.")
                    raw, blob, retrieval = canonical, canonical_hash, "git_blob"
                if raw.splitlines()[:1] == [b"version https://git-lfs.github.com/spec/v1"]:
                    raise AuditError("Snapshot incompleto: puntero LFS sin contenido; no se inicia el análisis.")
                target = source.joinpath(*PurePosixPath(path).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)  # Links are metadata files; never followed or executed.
                try:
                    text = raw.decode("utf-8") if b"\0" not in raw else None
                except UnicodeError:
                    text = None
                if text is None:
                    kind = "binary"
                records.append({"path": path, "text": text, "kind": kind})
                inventory.append({"path": path, "kind": kind, "bytes": len(raw), "git_blob": blob,
                                  "sha256": hashlib.sha256(raw).hexdigest(), "retrieval": retrieval})
                seen.add(path)
        if seen != set(expected):
            raise AuditError("Snapshot incompleto: faltan archivos del árbol; no se inicia el análisis.")
        return {"repository": f"https://github.com/{owner}/{repo}", "branch": branch, "commit": commit["sha"],
                "files": records, "inventory": inventory, "excluded": [], "tree_files": len(expected),
                "bytes_downloaded": sum(x["bytes"] for x in inventory), "acquisition_complete": True,
                "acquisition_seconds": round(time.monotonic() - started, 3),
                "acquisition_limits": {"bytes": maximum, "files": maximum_files, "seconds": seconds}}
    except (OSError, tarfile.TarError, ValueError) as exc:
        raise AuditError("Snapshot incompleto: descarga o archivo inválido; no se inicia el análisis.") from exc
    finally:
        archive.unlink(missing_ok=True)


from contextlib import contextmanager
import shutil
import tempfile


@contextmanager
def snapshot_workspace():
    """Called under the audit lock; recover only our own interrupted workspaces."""
    root = Path(tempfile.gettempdir()) / ("arktic-snapshots-" + str(os.getuid()))
    if root.is_symlink():
        raise AuditError("Directorio temporal de snapshots inseguro.")
    root.mkdir(mode=0o700, exist_ok=True)
    if root.stat().st_uid != os.getuid():
        raise AuditError("Directorio temporal pertenece a otro usuario.")
    for old in root.iterdir():
        if old.name.startswith("job-") and old.is_dir() and not old.is_symlink():
            shutil.rmtree(old)
    with tempfile.TemporaryDirectory(prefix="job-", dir=root) as directory:
        yield Path(directory)
