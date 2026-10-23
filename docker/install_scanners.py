"""Install immutable upstream Linux/amd64 releases; fail closed on hash mismatch."""
import hashlib
import io
import os
from pathlib import Path
import tarfile
from urllib.request import urlopen

RELEASES = [
    ("gitleaks", "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz", "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"),
    ("osv-scanner", "https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64", "160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b"),
]
for name, url, digest in RELEASES:
    with urlopen(url, timeout=90) as response:
        raw = response.read(150_000_000)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise RuntimeError("Scanner release checksum mismatch: " + name)
    if url.endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            raw = archive.extractfile("gitleaks").read()
    path = Path("/usr/local/bin") / name
    path.write_bytes(raw)
    os.chmod(path, 0o755)
