"""Block 2 experiment: bounded snapshots and offline AST extraction, no agents."""
import argparse
from collections import Counter
import hashlib
from importlib.metadata import distributions, version
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import signal
import subprocess
import tarfile
import time
from urllib.request import Request, urlopen

CONFIG = json.loads((Path(__file__).parent / "indexer.json").read_text())
LIMITS = CONFIG["limits"]
WORK = Path("/work")
SKIP_DIRS = {".git", "node_modules", ".venv", "vendor", "dist", "build", "target", ".next", "reports", "artifacts", "__pycache__"}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def unpack(archive, target, *, exclude=True):
    """Never materialize links, devices or paths outside the fresh snapshot."""
    if target.exists():
        raise ValueError(f"Destination already exists: {target}")
    target.mkdir(parents=True)
    total = 0
    count = 0
    members = 0
    expanded = 0
    skipped = []
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            members += 1
            expanded += member.size
            if members > LIMITS["files"] * 2 or expanded > LIMITS["snapshot_bytes"]:
                raise ValueError("Archive expansion budget exceeded")
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] in {"/", ".."} or ".." in parts or "\\" in member.name:
                raise ValueError("Unsafe archive path")
            rel = PurePosixPath(*parts[1:])
            if not str(rel) or str(rel) == "." or member.isdir():
                continue
            if not member.isfile():
                skipped.append({"path": str(rel), "reason": "not_regular_file"})
                continue
            if exclude and (set(rel.parts) & SKIP_DIRS or rel.name.startswith(".env") or rel.suffix in {".pem", ".key", ".p12", ".pfx"}):
                skipped.append({"path": str(rel), "reason": "excluded"})
                continue
            if member.size > LIMITS["file_bytes"]:
                skipped.append({"path": str(rel), "reason": "file_size_limit"})
                continue
            count += 1
            total += member.size
            if count > LIMITS["files"] or total > LIMITS["snapshot_bytes"]:
                raise ValueError("Snapshot budget exceeded")
            dest = target.joinpath(*rel.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as src, dest.open("xb") as out:
                remaining = member.size
                while remaining:
                    chunk = src.read(min(65536, remaining))
                    if not chunk:
                        raise ValueError("Truncated archive")
                    out.write(chunk)
                    remaining -= len(chunk)
    return {"files": count, "bytes": total, "skipped": skipped}


def download(repository, commit, target, *, exclude=True):
    if not re.fullmatch(r"[\w-]+/[\w.-]+", repository) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected GitHub owner/repository and full commit SHA")
    archive = target.parent / (target.name + ".tar.gz")
    url = f"https://codeload.github.com/{repository}/tar.gz/{commit}"
    digest = hashlib.sha256()
    received = 0
    start = time.monotonic()
    with urlopen(Request(url, headers={"User-Agent": "Arktic-Indexer-Validation"}), timeout=30) as response, archive.open("xb") as out:
        while chunk := response.read(65536):
            received += len(chunk)
            if received > LIMITS["archive_bytes"] or time.monotonic() - start > LIMITS["seconds"]:
                raise ValueError("Download budget exceeded")
            digest.update(chunk)
            out.write(chunk)
    result = unpack(archive, target, exclude=exclude)
    archive.unlink()
    return {**result, "archive_bytes": received, "archive_sha256": digest.hexdigest(), "download_extract_seconds": round(time.monotonic() - start, 3)}


def run(command, cwd, log, seconds=600):
    start = time.monotonic()
    with log.open("w") as output:
        process = subprocess.Popen(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            return {"exit_code": None, "timeout": True, "seconds": round(time.monotonic() - start, 3)}
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    return {"exit_code": code, "timeout": False, "seconds": round(time.monotonic() - start, 3)}


def install_source():
    # Source retrieval and all package installation happen only in docker build.
    download("Graphify-Labs/graphify", CONFIG["graphify"]["commit"], Path("/opt/graphify"), exclude=False)


def fetch():
    write_json(WORK / "environment.json", {"graphify": version("graphifyy"),
               "python": os.sys.version, "packages": sorted((d.metadata["Name"], d.version) for d in distributions())})
    for sample in CONFIG["samples"]:
        folder = WORK / sample["id"]
        folder.mkdir()  # Refuse accidental reuse of prior outputs.
        start = time.monotonic()
        manifest = {**sample, "graphify": CONFIG["graphify"], "limits": LIMITS, "status": "fetching"}
        try:
            signal.alarm(LIMITS["seconds"])
            manifest.update(download(sample["repository"], sample["commit"], folder / "snapshot"))
            if sample.get("patch"):
                patch = Path("/app") / sample["patch"]
                manifest["patch_sha256"] = hashlib.sha256(patch.read_bytes()).hexdigest()
                result = run(["git", "apply", "--check", str(patch)], folder / "snapshot", folder / "patch-check.log")
                if result["exit_code"] != 0:
                    raise RuntimeError("Frontend patch check failed")
                result = run(["git", "apply", str(patch)], folder / "snapshot", folder / "patch.log")
                if result["exit_code"] != 0:
                    raise RuntimeError("Frontend patch failed")
            manifest["status"] = "ready"
        except Exception as exc:
            manifest.update(status="error", error=str(exc))
            raise
        finally:
            signal.alarm(0)
            manifest["fetch_seconds"] = round(time.monotonic() - start, 3)
            write_json(folder / "snapshot.json", manifest)


def summarize(graph, snapshot):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", graph.get("links", []))
    sources = set()
    for node in nodes:
        value = node.get("source_file")
        if value:
            sources.add(str(value).removeprefix(str(snapshot) + "/"))
    inventory = Counter()
    represented = Counter()
    files = []
    for path in sorted(snapshot.rglob("*")):
        if path.is_file():
            name = path.relative_to(snapshot).as_posix()
            ext = path.suffix.lower() or "(no extension)"
            inventory[ext] += 1
            if name in sources:
                represented[ext] += 1
            files.append({"path": name, "extension": ext, "represented": name in sources})
    return {"nodes": len(nodes), "edges": len(edges), "relations": dict(Counter(e.get("relation", "unknown") for e in edges)),
            "files_by_extension": dict(inventory), "represented_by_extension": dict(represented), "files": files}


def cgroup(name):
    path = Path("/sys/fs/cgroup") / name
    legacy = {"memory.max": "memory.limit_in_bytes", "memory.peak": "memory.max_usage_in_bytes", "memory.events": "memory.failcnt"}
    if not path.is_file() and name in legacy:
        path = Path("/sys/fs/cgroup/memory") / legacy[name]
    return path.read_text().strip() if path.is_file() else None


def index(sample_id):
    sample = next(s for s in CONFIG["samples"] if s["id"] == sample_id)
    folder = WORK / sample_id
    manifest = json.loads((folder / "snapshot.json").read_text())
    if manifest["status"] != "ready" or manifest["commit"] != sample["commit"]:
        raise ValueError("Missing or incompatible snapshot")
    snapshot = folder / "snapshot"
    result = folder / "result"
    result.mkdir()
    # No target-installed dependencies, configuration hooks or LLM backend.
    os.environ.update(GRAPHIFY_BACKEND="none", GRAPHIFY_QUERY_LOG_DISABLE="1", PYTHONHASHSEED="0")
    if version("graphifyy") != CONFIG["graphify"]["version"]:
        raise ValueError("Installed Graphify version differs from pinned configuration")
    resource.setrlimit(resource.RLIMIT_FSIZE, (64_000_000, 64_000_000))
    command = ["graphify", "extract", str(snapshot), "--code-only", "--no-cluster", "--max-workers", str(LIMITS["workers"]), "--out", str(result)]
    metrics = {"sample": sample, "graphify": CONFIG["graphify"], "command": command,
               "memory_limit_bytes": cgroup("memory.max"), "network": "none", "models": "disabled"}
    metrics.update(run(command, snapshot, result / "extract.log", LIMITS["seconds"]))
    graph_path = result / "graphify-out/graph.json"
    if metrics["exit_code"] == 0 and graph_path.is_file():
        graph = json.loads(graph_path.read_text())
        metrics.update(summarize(graph, snapshot))
        metrics["queries"] = []
        for number, query in enumerate(sample["queries"]):
            outcome = run(["graphify", "query", query, "--budget", "2000", "--graph", str(graph_path)], snapshot, result / f"query-{number}.txt", 30)
            item = {"query": query, **outcome}
            # One bounded, deterministic disambiguation, never a model request.
            if outcome["exit_code"] == 3:
                candidates = [n for n in graph["nodes"] if n.get("label", "").removesuffix("()") == query]
                if len(candidates) == 1:
                    seed = candidates[0]["id"]
                    item["scoped"] = {"seed": seed, **run(["graphify", "query", query, "--seed", seed, "--budget", "2000", "--graph", str(graph_path)], snapshot, result / f"query-{number}-scoped.txt", 30)}
            metrics["queries"].append(item)
        metrics["probes"] = evaluate(graph, snapshot, sample_id)
    else:
        metrics["error"] = "Extraction failed or graph missing; see extract.log"
    metrics["container_memory_peak_bytes"] = cgroup("memory.peak")
    metrics["memory_events"] = cgroup("memory.events")
    metrics["child_max_rss_kib"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    metrics["child_cpu_seconds"] = round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime, 3)
    metrics["diagnostic_lines"] = [line for line in (result / "extract.log").read_text().splitlines() if any(term in line.lower() for term in ("warning", "error", "not classified", "skipping"))]
    metrics["graph_bytes"] = graph_path.stat().st_size if graph_path.exists() else 0
    write_json(result / "metrics.json", metrics)
    print(json.dumps({k: v for k, v in metrics.items() if k not in {"files", "command"}}, ensure_ascii=False))
    queries_ok = all(q.get("scoped", q)["exit_code"] == 0 for q in metrics.get("queries", []))
    return 0 if metrics["exit_code"] == 0 and metrics.get("nodes", 0) > 0 and queries_ok else 1


def evaluate(graph, snapshot, sample_id):
    """Small source-backed probes, not a claim of complete graph accuracy."""
    probes = json.loads((Path(__file__).parent / "probes.json").read_text())[sample_id]
    nodes = {n["id"]: n for n in graph["nodes"]}
    results = []
    for probe in probes:
        source = snapshot / probe["source_file"]
        evidence = [{"line": i, "text": line.strip()} for i, line in enumerate(source.read_text().splitlines(), 1) if probe["text"] in line]
        matches = []
        for edge in graph.get("edges", graph.get("links", [])):
            origin = nodes.get(edge["source"], {})
            target = nodes.get(edge["target"], {})
            if (edge.get("relation") == probe["relation"] and origin.get("source_file") == probe["source_file"]
                    and origin.get("label") == probe["source_label"] and target.get("source_file") == probe["target_file"]
                    and target.get("label") == probe["target_label"]):
                matches.append(edge)
        results.append({**probe, "evidence": evidence, "recovered": bool(evidence and matches), "edges": matches})
    return results


def deadline_exceeded(*_):
    raise TimeoutError("Snapshot time budget exceeded")


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, deadline_exceeded)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["install-source", "fetch", "index"])
    parser.add_argument("sample", nargs="?", choices=[s["id"] for s in CONFIG["samples"]])
    args = parser.parse_args()
    if args.mode == "install-source":
        install_source()
    elif args.mode == "fetch":
        fetch()
    elif not args.sample:
        parser.error("index requires one sample per container for separate memory peaks")
    else:
        raise SystemExit(index(args.sample))
