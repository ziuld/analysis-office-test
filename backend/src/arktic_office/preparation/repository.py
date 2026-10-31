"""Immutable acquisition and independent bounded context selection."""
import base64
from arktic_office.core.errors import AuditError, GitHubNotFound
from arktic_office.core.contracts import EvidenceSnapshot
import json
import os
import re
import time
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_FILES = 24
MAX_FILE_BYTES = 12_000
MAX_TOTAL_BYTES = 120_000
MAX_DOWNLOAD_BYTES = 256_000
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Cargo.lock", "go.sum", "Gemfile.lock", "composer.lock"}
MAX_RESPONSE = 3_000_000
SKIP_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".next", "coverage", "tests", "test", "__tests__", "fixtures"}
MANIFESTS = {"package.json", "pom.xml", "requirements.txt", "pyproject.toml", "go.mod",
             "Cargo.toml", "Gemfile", "composer.json", "Dockerfile", "Procfile",
             "compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml",
             "build.gradle", "settings.gradle", "build.gradle.kts", "settings.gradle.kts"}
SOURCE_EXT = {".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".go", ".cs", ".rb", ".php"}






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
    if p.suffix in SOURCE_EXT and any(word in path.lower() for word in ("auth", "security", "middleware", "controller", "route", "service", "repository")):
        return 0
    if name.lower().startswith("readme"):
        return 0
    if name in MANIFESTS or name in LOCKFILES:
        return 1
    if name in {"index.js", "index.ts", "main.py", "app.py", "server.js", "server.ts", "main.go", "Program.cs", "Application.java"}:
        return 2
    if p.suffix in {".yml", ".yaml", ".toml", ".xml", ".properties"}:
        return 2
    if p.suffix in SOURCE_EXT:
        return 4 if "scripts" in p.parts else 3
    return 9


def file_role(path):
    """Structural coverage, independent of README content or framework detection."""
    p = PurePosixPath(path)
    name, lower = p.name.lower(), path.lower()
    if p.name in LOCKFILES:
        return "lock"
    if name.startswith("dockerfile") or name in {"compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml", "procfile"}:
        return "deployment"
    if p.name in MANIFESTS:
        return "manifest"
    if "/providers/" in lower:
        return "config"
    if any(x in lower for x in ("database", "migration", "models/", "model/")) or name in {"user.php", "theme.php"}:
        return "data"
    if name in {"index.js", "index.ts", "index.php", "main.py", "app.py", "server.js", "server.ts", "server.php", "main.go", "program.cs", "application.java", "artisan"} or lower.endswith("bootstrap/app.php"):
        return "entry"
    if "route" in lower or name == "kernel.php":
        return "routes"
    if "controller" in lower or "service" in lower and "providers/" not in lower and "config/" not in lower:
        return "business"
    if any(x in lower for x in ("auth", "security", "middleware", "permission")):
        return "security"
    if "config" in p.parts or p.suffix in {".yaml", ".yml", ".toml", ".properties", ".xml"}:
        return "config"
    if name.startswith("readme"):
        return "readme"
    return "source"


def balanced_files(items, roles):
    """Round-robin categories so many middleware files cannot displace manifests/data."""
    groups = {role: [] for role in roles}
    for item in items:
        role = file_role(item["path"])
        if role in groups:
            groups[role].append(item)
    for role, group in groups.items():
        if role == "data":
            group.sort(key=lambda x: 0 if any(w in PurePosixPath(x["path"]).name.lower() for w in ("database", "datasource")) else 1)
        elif role == "business":
            group.sort(key=lambda x: (PurePosixPath(x["path"]).name.lower() in {"controller.php", "controller.py", "basecontroller.php"}, x["path"].lower().startswith(("public/", "resources/", "static/"))))
    result = []
    while any(groups.values()):
        for role in roles:
            if groups[role]:
                result.append(groups[role].pop(0))
    return result


def exclusion(item):
    path = PurePosixPath(item["path"])
    if item.get("mode") not in {"100644", "100755"}:
        return "enlace, submódulo u otro modo no admitido"
    if any(part in SKIP_DIRS for part in path.parts):
        return "dependencia o archivo generado"
    name = path.name.lower()
    if name in {"osv-scanner.toml", ".gitleaks.toml", ".gitleaksignore"}:
        return "configuración de scanner del repositorio no confiable"
    if (name.startswith(".env") or name.endswith((".pem", ".key", ".p12", ".pfx"))
            or any(word in name for word in ("credentials", "secrets", "id_rsa"))):
        return "archivo potencialmente sensible"
    if item.get("size", MAX_DOWNLOAD_BYTES + 1) > MAX_DOWNLOAD_BYTES:
        return "supera 256 KB de descarga acotada"
    if priority(item["path"]) == 9:
        return "fuera de la selección inicial"
    return None


def redact(text):
    """Compatibility name: analysis content is preserved exactly, by user decision."""
    return text


def excerpt(content, budget=MAX_FILE_BYTES):
    """Keep original line positions; omitted lines are blank, never invented evidence."""
    lines = content.splitlines()
    if len(content.encode()) <= budget:
        return content, False
    important = re.compile(r"auth|permission|role|route|request|query|execute|select |password|token|secret|upload|fetch\(|https?://|permitAll|mapping|database", re.I)
    wanted = set(range(min(30, len(lines))))
    for i, line in enumerate(lines):
        if important.search(line):
            wanted.update(range(max(0, i - 3), min(len(lines), i + 5)))
    selected, size = {}, len(lines)
    for i in sorted(wanted):
        length = len(lines[i].encode())
        if size + length <= budget:
            selected[i] = lines[i]
            size += length
    return "\n".join(selected.get(i, "") for i in range(len(lines))), True


def selection_limits():
    try:
        max_files = int(os.environ.get("AUDIT_MAX_FILES", str(MAX_FILES)))
        max_total = int(os.environ.get("AUDIT_MAX_TOTAL_BYTES", str(MAX_TOTAL_BYTES)))
    except ValueError:
        raise AuditError("Los límites de lectura deben ser números enteros.") from None
    if not 1 <= max_files <= 40 or not 12000 <= max_total <= 200000:
        raise AuditError("Límites admitidos: 1–40 archivos y 12000–200000 bytes totales.")
    return max_files, max_total


def acquire(url, fetch=github, *, hybrid=False):
    started = time.monotonic()
    max_files, max_total = selection_limits()
    if hybrid:
        max_files, max_total = 120, 1_000_000
    owner, repo = parse_repo(url)
    root = f"/repos/{owner}/{repo}"
    branch = fetch(root).get("default_branch")
    if not isinstance(branch, str) or not branch:
        raise AuditError("GitHub no declaró una rama predeterminada válida.")
    commit = fetch(root + "/branches/" + quote(branch, safe=""))["commit"]
    sha = commit["sha"]
    tree = fetch(root + "/git/trees/" + commit["commit"]["tree"]["sha"] + "?recursive=1")
    if tree.get("truncated"):
        raise AuditError("GitHub devolvió un árbol incompleto; el MVP no lo analizará como si estuviera completo.")
    excluded, used = [], 0
    raw_files, downloaded = [], 0
    blobs = [x for x in tree["tree"] if x["type"] in {"blob", "commit"}]
    ordered = sorted(blobs, key=lambda x: (priority(x["path"]), len(PurePosixPath(x["path"]).parts), x["path"]))
    ordered = balanced_files(ordered, ("manifest", "manifest", "deployment", "entry", "data", "routes", "business", "security", "config", "lock", "source", "readme"))
    failure = None
    for item in ordered:
        reason = exclusion(item)
        if not reason and (failure or time.monotonic() - started > 180):
            reason = failure or "tiempo de adquisición agotado"
        if not reason and (len(raw_files) >= max_files or used + min(item["size"], MAX_FILE_BYTES) > max_total or downloaded + item["size"] > 1000000):
            reason = "límite de archivos o presupuesto de lectura"
        if reason:
            excluded.append({"path": item["path"], "reason": reason})
            continue
        try:
            blob = fetch(root + "/git/blobs/" + item["sha"])
        except AuditError:
            failure = "adquisición interrumpida por error de GitHub; evidencia parcial"
            excluded.append({"path": item["path"], "reason": failure})
            continue
        try:
            if blob.get("encoding") != "base64":
                raise ValueError()
            raw = base64.b64decode(blob["content"], validate=False)
            if len(raw) > MAX_DOWNLOAD_BYTES or downloaded + len(raw) > 1000000 or b"\0" in raw:
                raise ValueError()
            content = raw.decode("utf-8")
        except (ValueError, UnicodeError):
            excluded.append({"path": item["path"], "reason": "contenido binario, inválido o demasiado grande"})
            continue
        downloaded += len(raw)
        raw_files.append({"path": item["path"], "text": content})
        used += min(len(raw), MAX_FILE_BYTES)
    return {"repository": f"https://github.com/{owner}/{repo}", "branch": branch, "commit": sha,
            "files": raw_files, "excluded": excluded, "bytes_downloaded": downloaded,
            "tree_files": len(blobs), "acquisition_seconds": round(time.monotonic() - started, 3),
            "acquisition_limits": {"files": max_files, "bytes": 1_000_000, "seconds": 180,
                                   "request_timeout_seconds": 30}}


def select(snapshot, scanner=None) -> EvidenceSnapshot:
    """No network: scanner input and model selection have explicit, different scopes."""
    max_files, max_total = selection_limits()
    raw_files = snapshot["files"]
    scanner_results = scanner(raw_files) if scanner and raw_files else []
    files, used, excluded = [], 0, list(snapshot["excluded"])
    for file in raw_files:
        selected, partial = excerpt(redact(file["text"]))
        length = len(selected.encode())
        if len(files) >= max_files or length > MAX_FILE_BYTES or used + length > max_total:
            excluded.append({"path": file["path"], "reason": "presupuesto de contexto inicial"})
            continue
        files.append({"path": file["path"], "text": selected, "partial": partial})
        used += length
    mask_findings(files, scanner_results)
    bounded, used = [], 0
    for file in files:
        length = len(file["text"].encode())
        if length > MAX_FILE_BYTES or used + length > max_total:
            excluded.append({"path": file["path"], "reason": "ocultación supera presupuesto de contexto"})
            continue
        bounded.append(file)
        used += length
    files = bounded
    return {**snapshot, "files": files, "excluded": excluded, "bytes_read": used,
            "scanners": scanner_results,
            "coverage": {"acquired": [f["path"] for f in raw_files],
                         "scanner_input": [f["path"] for f in raw_files] if scanner else [],
                         "model_candidates": [f["path"] for f in files],
                         "scanner_executed": bool(scanner and raw_files)},
            "limits": {"files": max_files, "file_bytes": MAX_FILE_BYTES, "total_bytes": max_total}}


def mask_findings(files, scanner_results):
    """Scanner findings never replace or obscure the captured source."""
    return None


def collect(url, fetch=github, scanner=None) -> EvidenceSnapshot:
    return select(acquire(url, fetch), scanner)
