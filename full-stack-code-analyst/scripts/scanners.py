"""Deterministic tools over a private snapshot; results are cached by effective input."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from storage import (KIT, LOCAL, artifacts, digest, environment, file_hash, intact, now, protect,
                     read_json, write_json)

VERSIONS = read_json(KIT / "tools/versions.json")
LOCKS = {"pnpm-lock.yaml", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "bun.lock",
         "uv.lock", "poetry.lock", "Pipfile.lock", "requirements.txt", "Cargo.lock", "go.mod",
         "go.sum", "composer.lock", "Gemfile.lock", "packages.lock.json", "pom.xml", "pubspec.lock"}
SAST = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".php", ".go"}


def executable(tool):
    spec = VERSIONS[tool]
    record = read_json(LOCAL / "tools" / tool / "installation.json", {})
    candidate = Path(record.get("executable", "")) if record else None
    if candidate and not candidate.is_absolute():
        candidate = LOCAL / candidate
    if candidate and candidate.is_file() and candidate.resolve().is_relative_to(LOCAL.resolve()):
        return str(candidate.resolve())
    return shutil.which(spec["command"])


def tool_info(tool):
    binary = executable(tool)
    if not binary:
        return {"status": "missing", "requested_version": VERSIONS[tool]["version"]}
    try:
        result = subprocess.run([binary, "--version"], capture_output=True, timeout=20,
                                env=environment(LOCAL / "cache/probes"))
        version = re.search(r"\b\d+\.\d+\.\d+\b", (result.stdout + result.stderr).decode("utf-8", "replace"))
        if result.returncode or not version:
            log = LOCAL / "cache/probes" / (tool + "-version.log")
            log.write_text(protect((result.stdout + result.stderr).decode("utf-8", "replace")), encoding="utf-8")
            return {"status": "unavailable", "executable": binary, "exit_code": result.returncode,
                    "diagnostic": str(log)}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "executable": binary}
    return {"status": "available", "version": version[0], "executable": binary}


def selected_files(tool, source):
    files = [item for item in source["files"] if item["kind"] == "text"]
    if tool == "osv":
        return [item for item in files if Path(item["path"]).name in LOCKS
                or re.fullmatch(r"requirements[^/]*\.txt", Path(item["path"]).name)]
    if tool == "semgrep":
        return [item for item in files if Path(item["path"]).suffix.lower() in SAST]
    if tool == "graphify":
        return [item for item in files if not Path(item["path"]).name.startswith(".env")]
    return files


def signature(tool, source, info):
    version = info.get("version", VERSIONS[tool]["version"])
    identity = {"tool": tool, "version": version, "project": source["root"],
                "files": selected_files(tool, source), "adapter": file_hash(Path(__file__)),
                "protection": file_hash(KIT / "scripts/storage.py"), "mode": "static"}
    if tool == "semgrep":
        identity["rules"] = file_hash(KIT / "tools/semgrep-rules.json")
        identity["engine"] = info.get("engine", "local")
        if info.get("engine") == "docker":
            identity["image"] = info.get("image")
            identity["image_id"] = info.get("image_id")
            identity["container_adapter"] = file_hash(KIT / "scripts/semgrep_docker.py")
    return digest(identity)


def cached(tool, source, info):
    key = signature(tool, source, info)
    folder = LOCAL / "cache" / tool / key[:16]
    pointer = read_json(folder / "pointer.json", {})
    name = pointer.get("folder", "")
    if pointer.get("key") == key and name and Path(name).name == name:
        candidate = folder.parent / name
        if candidate.resolve().parent == folder.resolve().parent and not candidate.is_symlink():
            folder = candidate
    state = read_json(folder / "estado.json", {})
    usable = (state.get("key") == key and state.get("status") == "complete" and intact(folder, state))
    stale = False
    if tool == "osv" and usable:
        try:
            stale = datetime.now(timezone.utc) - datetime.fromisoformat(state["finished_at"]) > timedelta(days=7)
        except (ValueError, KeyError):
            stale = True
    return folder, state, usable, stale


def copy_input(source, folder, tool):
    folder.mkdir()
    for item in selected_files(tool, source):
        original = Path(source["root"]) / item["path"]
        raw = original.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("El código cambió durante la preparación; vuelve a comprobar el estado.")
        if tool != "gitleaks":
            raw = protect(raw.decode("utf-8")).encode("utf-8")
        destination = folder / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)


def safe_value(value, source=None):
    if isinstance(value, dict):
        return {key: "<valor protegido>" if key in {"Secret", "Match"} else safe_value(child, source)
                for key, child in value.items()}
    if isinstance(value, list):
        return [safe_value(child, source) for child in value]
    if isinstance(value, str):
        if source:
            value = value.replace(str(source) + os.sep, "").replace(source.as_posix() + "/", "")
        return protect(value)
    return value


def command(tool, binary, source, folder):
    target = folder / "input"
    raw = folder / "resultado.json"
    if tool == "graphify":
        # A nested repository prevents a parent's ignore rules hiding the copied corpus.
        init = subprocess.run(["git", "init", "-q", str(target)], capture_output=True,
                              env=environment(folder / "home"), timeout=30)
        if init.returncode:
            raise ValueError("Graphify necesita Git para aislar las reglas de exclusión de la copia.")
        return [binary, "update", str(target), "--no-cluster"], target / "graphify-out/graph.json"
    if tool == "gitleaks":
        config = folder / "gitleaks.toml"
        config.write_text("[extend]\nuseDefault = true\n", encoding="utf-8")
        return [binary, "dir", str(target), "--config", str(config), "--ignore-gitleaks-allow",
                "--redact=100", "--no-banner", "--report-format", "json", "--report-path", str(raw)], raw
    if tool == "semgrep":
        (target / ".semgrepignore").write_text("", encoding="utf-8")
        return [binary, "scan", "--oss-only", "--config", str(KIT / "tools/semgrep-rules.json"),
                "--json", "--output", str(raw), "--metrics=off", "--disable-version-check",
                "--no-git-ignore", "--no-rewrite-rule-ids", "--jobs=2", "--timeout=10",
                "--max-target-bytes=2000000", str(target)], raw
    files = selected_files("osv", source)
    config = folder / "osv.toml"
    config.write_text("", encoding="utf-8")
    args = []
    for item in files:
        path = target / item["path"]
        name = path.name
        prefix = "requirements.txt:" if name.startswith("requirements") and name.endswith(".txt") else ""
        args.append("--lockfile=" + prefix + str(path))
    return [binary, "scan", "source", "--no-call-analysis=all", "--all-packages",
            "--config=" + str(config), "--format=json", "--output-file=" + str(raw), *args], raw


def run_tool(tool, source, *, refresh=False, online=False, semgrep_engine="local", allow_image_download=False):
    if tool == "semgrep" and semgrep_engine == "skip":
        return {"status": "skipped", "engine": "skip", "reason": "user_choice", "cache": "unavailable"}
    docker = tool == "semgrep" and semgrep_engine == "docker"
    if docker:
        import semgrep_docker
        info = semgrep_docker.info()
        if info["status"] == "needs_image_download" and allow_image_download:
            info = semgrep_docker.pull()
    else:
        info = tool_info(tool)
    folder, state, reusable, stale = cached(tool, source, info)
    if reusable and not refresh:
        return {**state, "cache": "reused", "stale": stale, "folder": str(folder)}
    if tool == "osv" and not online:
        return {"status": "needs_network_consent", "cache": "unavailable"}
    if info["status"] != "available":
        return {**info, "cache": "unavailable"}
    # Interrupted or failed attempts remain inspectable, with a fresh working directory.
    if folder.exists():
        folder = folder.with_name(folder.name + "-" + uuid.uuid4().hex[:6])
    folder.mkdir(parents=True)
    state = {"tool": tool, "key": signature(tool, source, info), "version": info["version"],
             "status": "running", "started_at": now(), "input_count": len(selected_files(tool, source))}
    if tool == "semgrep":
        state.update(engine=semgrep_engine, image=info.get("image"), image_id=info.get("image_id"))
    write_json(folder / "estado.json", state)
    container_name = None
    try:
        copy_input(source, folder / "input", tool)
        if not selected_files(tool, source):
            write_json(folder / "resultado.json", {"findings": [], "reason": "no_compatible_inputs"})
            state.update(status="complete", coverage="no_compatible_inputs")
        else:
            if docker:
                args, raw, container_name = semgrep_docker.command(info, folder)
            else:
                args, raw = command(tool, info["executable"], source, folder)
            result = subprocess.run(args, capture_output=True, timeout=600, cwd=folder,
                                    **({} if docker else {"env": environment(folder / "home")}))
            # Raw process output is sanitized before persistence.
            (folder / "ejecucion.log").write_text(protect((result.stdout + result.stderr).decode("utf-8", "replace")),
                                                 encoding="utf-8")
            state["exit_code"] = result.returncode
            if result.returncode not in ({0} if tool == "graphify" else {0, 1}):
                raise ValueError("La herramienta terminó con error; consulta el log local.")
            if not raw.is_file() or raw.stat().st_size > 64_000_000:
                raise ValueError("Resultado ausente o fuera del límite de capacidad.")
            payload = json.loads(raw.read_text(encoding="utf-8"))
            valid = isinstance(payload, list) if tool == "gitleaks" else isinstance(payload, dict)
            if tool == "graphify":
                valid = valid and isinstance(payload.get("nodes"), list) and (
                    isinstance(payload.get("edges"), list) or isinstance(payload.get("links"), list))
            if tool in {"semgrep", "osv"}:
                valid = valid and isinstance(payload.get("results"), list)
            if not valid:
                raise ValueError("La herramienta devolvió un formato inesperado.")
            if docker and payload.get("version") != info["version"]:
                raise ValueError("La versión de Semgrep del contenedor no coincide con la declarada.")
            write_json(folder / "resultado.json", safe_value(payload, Path("/src") if docker else folder / "input"))
            if tool == "semgrep" and payload.get("errors"):
                raise ValueError("Semgrep informó errores de análisis; el resultado queda parcial.")
            state.update(status="complete", coverage="tool_native_limits")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        state.update(status="error", error=protect(str(exc)))
    finally:
        if container_name:
            state["container_cleanup"] = semgrep_docker.cleanup(info["executable"], container_name)
            if state["container_cleanup"]["status"] == "cleanup_failed":
                state.update(status="error", error="No se pudo confirmar la eliminación del contenedor.",
                             container_name=container_name)
    state["finished_at"] = now()
    # Fingerprint the delivered result and log, leaving native caches and inputs private.
    state["artifacts"] = {p.name: file_hash(p) for p in (folder / "resultado.json", folder / "ejecucion.log")
                          if p.is_file()}
    write_json(folder / "estado.json", state)
    # Replace the canonical cache only after a complete successful retry.
    canonical = LOCAL / "cache" / tool / state["key"][:16]
    if state["status"] == "complete" and folder != canonical:
        write_json(canonical / "pointer.json", {"folder": folder.name, "key": state["key"]})
    return {**state, "folder": str(folder), "cache": "generated", "stale": False}
