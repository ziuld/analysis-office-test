"""Bounded GitHub reader: main, or master only when main is absent."""
import base64
import json
import os
import re
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_FILES = 12
MAX_FILE_BYTES = 12_000
MAX_TOTAL_BYTES = 48_000
MAX_RESPONSE = 3_000_000
SKIP_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".next", "coverage", "tests", "test", "__tests__", "fixtures"}
MANIFESTS = {"package.json", "pom.xml", "requirements.txt", "pyproject.toml", "go.mod",
             "Cargo.toml", "Gemfile", "composer.json", "Dockerfile", "Procfile",
             "compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml",
             "build.gradle", "settings.gradle", "build.gradle.kts", "settings.gradle.kts"}
SOURCE_EXT = {".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".go", ".cs", ".rb", ".php"}


class AuditError(Exception):
    pass


class GitHubNotFound(AuditError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_repo(url):
    parsed = urlsplit(url)
    parts = parsed.path.rstrip("/").split("/")
    if (parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query
            or parsed.fragment or len(parts) != 3):
        raise AuditError("Introduce solo https://github.com/propietario/repositorio, sin rama ni parámetros.")
    owner, repo = parts[1], parts[2].removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or repo in {".", "..", ""}:
        raise AuditError("URL de repositorio no válida.")
    return owner, repo


def github(endpoint):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "arktic-office-mvp",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with build_opener(NoRedirect()).open(Request("https://api.github.com" + endpoint, headers=headers), timeout=30) as response:
            body = response.read(MAX_RESPONSE + 1)
    except HTTPError as exc:
        if exc.code == 404:
            raise GitHubNotFound("No se encontró el recurso de GitHub o falta acceso al repositorio.") from None
        if exc.code in (401, 403, 429):
            raise AuditError("GitHub denegó el acceso o alcanzó su límite de peticiones; revisa el token de lectura.") from None
        raise AuditError(f"GitHub devolvió HTTP {exc.code}; revisión interrumpida.") from None
    except (URLError, TimeoutError):
        raise AuditError("No se pudo contactar con GitHub dentro del tiempo permitido.") from None
    if len(body) > MAX_RESPONSE:
        raise AuditError("La respuesta de GitHub supera el límite del MVP.")
    try:
        return json.loads(body)
    except (ValueError, UnicodeError):
        raise AuditError("GitHub devolvió una respuesta no válida.") from None


def priority(path):
    p = PurePosixPath(path)
    name = p.name
    if (name.lower().startswith("test") or ".test." in name or ".spec." in name
            or name.startswith(("playwright.", "vitest."))
            or (".github" in p.parts and "workflows" not in p.parts)):
        return 9
    if name.lower().startswith("readme"):
        return 0
    if name in MANIFESTS:
        return 1
    if name in {"index.js", "index.ts", "main.py", "app.py", "server.js", "server.ts", "main.go", "Program.cs", "Application.java"}:
        return 2
    if p.suffix in {".yml", ".yaml", ".toml", ".xml", ".properties"}:
        return 2
    if p.suffix in SOURCE_EXT:
        return 4 if "scripts" in p.parts else 3
    return 9


def exclusion(item):
    path = PurePosixPath(item["path"])
    if item.get("mode") not in {"100644", "100755"}:
        return "enlace, submódulo u otro modo no admitido"
    if any(part in SKIP_DIRS for part in path.parts):
        return "dependencia o archivo generado"
    name = path.name.lower()
    if (name.startswith(".env") or name.endswith((".pem", ".key", ".p12", ".pfx"))
            or any(word in name for word in ("credentials", "secrets", "id_rsa"))):
        return "archivo potencialmente sensible"
    if item.get("size", MAX_FILE_BYTES + 1) > MAX_FILE_BYTES:
        return "supera 12 KB"
    if priority(item["path"]) == 9:
        return "fuera de la selección inicial"
    return None


def redact(text):
    """Conservative heuristic; not a complete secret scanner. Preserve line numbers."""
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
                  lambda m: "\n".join("[VALOR OCULTO]" for _ in m[0].split("\n")), text, flags=re.S)
    text = re.sub(r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,})", "[VALOR OCULTO]", text)
    text = re.sub(r"(://)[^\s/:@]+:[^\s/@]+@", r"\1[VALOR OCULTO]@", text)
    lines = []
    for line in text.splitlines():
        if re.search(r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token|authorization)\s*[\"']?\s*[:=]", line):
            line = "[LÍNEA CON POSIBLE CREDENCIAL OCULTA]"
        lines.append(line)
    return "\n".join(lines)


def collect(url, fetch=github):
    try:
        max_files = int(os.environ.get("AUDIT_MAX_FILES", str(MAX_FILES)))
        max_total = int(os.environ.get("AUDIT_MAX_TOTAL_BYTES", str(MAX_TOTAL_BYTES)))
    except ValueError:
        raise AuditError("Los límites de lectura deben ser números enteros.") from None
    if not 1 <= max_files <= 20 or not 12000 <= max_total <= 90000:
        raise AuditError("Límites admitidos: 1–20 archivos y 12000–90000 bytes totales.")
    owner, repo = parse_repo(url)
    root = f"/repos/{owner}/{repo}"
    branch = "main"
    try:
        commit = fetch(root + "/branches/main")["commit"]
    except GitHubNotFound:
        branch = "master"
        try:
            commit = fetch(root + "/branches/master")["commit"]
        except GitHubNotFound:
            # Distinguish missing branches from a missing/private repository.
            fetch(root)
            raise AuditError("El repositorio no tiene ninguna de las ramas admitidas: main o master.") from None
    sha = commit["sha"]
    tree = fetch(root + "/git/trees/" + commit["commit"]["tree"]["sha"] + "?recursive=1")
    if tree.get("truncated"):
        raise AuditError("GitHub devolvió un árbol incompleto; el MVP no lo analizará como si estuviera completo.")
    files, excluded, used = [], [], 0
    blobs = [x for x in tree["tree"] if x["type"] in {"blob", "commit"}]
    for item in sorted(blobs, key=lambda x: (priority(x["path"]), len(PurePosixPath(x["path"]).parts), x["path"])):
        reason = exclusion(item)
        if not reason and (len(files) >= max_files or used + item["size"] > max_total):
            reason = "límite de archivos o presupuesto de lectura"
        if reason:
            excluded.append({"path": item["path"], "reason": reason})
            continue
        blob = fetch(root + "/git/blobs/" + item["sha"])
        try:
            if blob.get("encoding") != "base64":
                raise ValueError()
            raw = base64.b64decode(blob["content"], validate=False)
            if len(raw) > MAX_FILE_BYTES or len(raw) + used > max_total or b"\0" in raw:
                raise ValueError()
            content = raw.decode("utf-8")
        except (ValueError, UnicodeError):
            excluded.append({"path": item["path"], "reason": "contenido binario, inválido o demasiado grande"})
            continue
        used += len(raw)
        files.append({"path": item["path"], "text": redact(content)})
    if not files:
        raise AuditError(f"No hay archivos de texto admitidos para revisar en {branch}.")
    return {"repository": f"https://github.com/{owner}/{repo}", "branch": branch, "commit": sha,
            "files": files, "excluded": excluded, "bytes_read": used,
            "limits": {"files": max_files, "file_bytes": MAX_FILE_BYTES, "total_bytes": max_total}}
