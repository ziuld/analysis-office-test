"""Install requested tools under Iris .local using official versioned distributions."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
from urllib.request import Request, urlopen
import zipfile
import uuid

from storage import LOCAL, environment, now, write_json
from scanners import VERSIONS


def download(url):
    if not url.startswith("https://"):
        raise ValueError("La descarga debe usar HTTPS.")
    with urlopen(Request(url, headers={"User-Agent": "Iris-local-tools"}), timeout=90) as response:
        raw = response.read(150_000_001)
    if len(raw) > 150_000_000:
        raise ValueError("La descarga supera el límite de 150 MB.")
    return raw


def install(tool):
    spec = VERSIONS[tool]
    base = LOCAL / "tools" / tool
    destination = base / spec["version"]
    if destination.exists():
        destination = base / (spec["version"] + "-" + uuid.uuid4().hex[:6])
    if tool == "semgrep" and os.name == "nt":
        raise ValueError("Esta distribución de Semgrep requiere Linux o macOS. Iris conservará ese análisis como pendiente en Windows.")
    if "package" in spec:
        uv = shutil.which("uv")
        if not uv:
            raise ValueError("Falta uv. Instálalo mediante el mecanismo habitual del equipo y repite la instalación local.")
        env = environment(LOCAL / "cache/installer")
        env.update(UV_CACHE_DIR=str(LOCAL / "cache/uv"), UV_PYTHON_INSTALL_DIR=str(LOCAL / "tools/python"),
                   UV_TOOL_DIR=str(LOCAL / "tools/uv"), UV_TOOL_BIN_DIR=str(LOCAL / "tools/bin"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        commands = ([uv, "venv", "--python", "3.12", str(destination)],
                    [uv, "pip", "install", "--python",
                     str(destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")),
                     "--index-url", "https://pypi.org/simple", spec["package"]])
        for command in commands:
            process = subprocess.run(command, env=env, capture_output=True, timeout=600)
            if process.returncode:
                raise ValueError("Falló la instalación Python aislada. Se conservan los archivos locales para diagnóstico.")
        binary = destination / ("Scripts" if os.name == "nt" else "bin") / (
            spec["command"] + (".exe" if os.name == "nt" else ""))
    else:
        system = {"Windows": "windows", "Linux": "linux", "Darwin": "darwin"}.get(platform.system())
        arch = {"AMD64": "amd64", "x86_64": "amd64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine())
        if not system or not arch:
            raise ValueError("No hay una distribución declarada para esta plataforma.")
        release = json.loads(download(f'https://api.github.com/repos/{spec["repository"]}/releases/tags/v{spec["version"]}'))
        arch_label = "x64" if tool == "gitleaks" and arch == "amd64" else arch
        if tool == "gitleaks":
            name = f'gitleaks_{spec["version"]}_{system}_{arch_label}.' + ("zip" if system == "windows" else "tar.gz")
        else:
            name = f"osv-scanner_{system}_{arch}" + (".exe" if system == "windows" else "")
        asset = next((a for a in release["assets"] if a["name"] == name), None)
        if not asset:
            raise ValueError("El release oficial no ofrece el binario esperado para esta plataforma.")
        raw = download(asset["browser_download_url"])
        expected = asset.get("digest", "")
        if expected.startswith("sha256:"):
            expected = expected[7:]
        else:
            checksum = next((a for a in release["assets"] if "checksum" in a["name"].lower()
                             or "sha256sums" in a["name"].lower()), None)
            if not checksum:
                raise ValueError("El release no aporta un checksum verificable.")
            lines = download(checksum["browser_download_url"]).decode().splitlines()
            matches = [line.split()[0] for line in lines if line.split()[-1].lstrip("*") == name]
            if len(matches) != 1:
                raise ValueError("No se encontró el checksum exacto del binario.")
            expected = matches[0]
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("El checksum del binario no coincide.")
        binary_name = spec["command"] + (".exe" if system == "windows" else "")
        if name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                raw = archive.read(binary_name)
        elif name.endswith(".tar.gz"):
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
                entry = archive.getmember(binary_name)
                if not entry.isfile():
                    raise ValueError("El binario del archivo tiene un tipo inesperado.")
                raw = archive.extractfile(entry).read()
        destination.mkdir(parents=True)
        binary = destination / binary_name
        binary.write_bytes(raw)
        binary.chmod(0o755)
    if not binary.is_file():
        raise ValueError("La instalación no produjo el ejecutable esperado.")
    record = {"tool": tool, "version": spec["version"], "executable": binary.relative_to(LOCAL).as_posix(),
              "installed_at": now(), "source": spec.get("repository", "PyPI"),
              "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()}
    write_json(base / "installation.json", record)
    return record
