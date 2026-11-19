"""Offline regression checks for the cache lifecycle using an isolated copy of Iris."""
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.dont_write_bytecode = True


def main():
    original = Path(__file__).resolve().parents[1]
    test_root = original / ".local/qa"
    test_root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="q-", dir=test_root, ignore_cleanup_errors=True) as directory:
        project = Path(directory)
        kit = project / "iris"
        shutil.copytree(original, kit, ignore=shutil.ignore_patterns(".local", "__pycache__", "*.pyc"))
        sys.path.insert(0, str(kit / "scripts"))
        import iris
        import scanners
        import storage
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")

        def git(*args):
            return subprocess.check_output(["git", "-C", str(project), "-c", "user.name=Iris QA",
                                             "-c", "user.email=iris@example.invalid", *args], env=env)

        git("init", "-q", "-b", "main")
        code = project / "app.py"
        code.write_text("def hola():\n    return 'hola'\n", encoding="utf-8")
        lockfile = project / "package-lock.json"
        lockfile.write_text('{"name":"fixture","lockfileVersion":3,"packages":{}}', encoding="utf-8")
        git("add", "app.py", "package-lock.json")
        git("commit", "-qm", "Fixture")
        source = storage.inventory(project)
        assert {item["path"] for item in source["files"]} == {"app.py", "package-lock.json"}
        info = {"status": "available", "version": "1.2.3", "executable": "fixture"}
        signature = scanners.signature("osv", source, info)
        code.write_text("def hola():\n    return 'cambio'\n", encoding="utf-8")
        changed = storage.inventory(project)
        assert changed["identity"] != source["identity"]
        assert scanners.signature("osv", changed, info) == signature
        assert scanners.signature("semgrep", changed, info) != scanners.signature("semgrep", source, info)
        code.write_text("def hola():\n    return 'hola'\n", encoding="utf-8")
        assert storage.inventory(project)["identity"] == source["identity"]
        git("switch", "-qc", "otra-rama")
        assert storage.inventory(project)["identity"] == source["identity"]
        git("commit", "--allow-empty", "-qm", "Commit sin cambiar contenido")
        assert storage.inventory(project)["identity"] == source["identity"]
        new_file = project / "nuevo.py"
        new_file.write_text("x = 1\n", encoding="utf-8")
        assert storage.inventory(project)["identity"] != source["identity"]
        new_file.unlink()
        assert scanners.signature("osv", source, {**info, "version": "1.2.4"}) != signature

        def invoke(*argv):
            with patch.object(sys, "argv", ["iris.py", *map(str, argv)]), StringIO() as capture:
                with redirect_stdout(capture), patch.object(iris.semgrep_docker, "probe", return_value={"status": "missing"}):
                    code = iris.main()
                assert code == 0, capture.getvalue()
                return json.loads(capture.getvalue())

        missing = {name: {"status": "missing", "requested_version": scanners.VERSIONS[name]["version"]}
                   for name in scanners.VERSIONS}
        with patch.object(iris, "tool_info", side_effect=lambda name: missing[name]):
            prepared = invoke("prepare", "--project", project, "--tools", "")
        review = Path(prepared["review"])
        assert prepared["tools"] == {}
        report = review / "informe-iris.html"
        invoke('render', '--review', review)
        invoke("finish", "--review", review, "--author", "fixture")
        with patch.object(iris, "tool_info", side_effect=lambda name: missing[name]):
            reused = invoke("prepare", "--project", project, "--tools", "")
            assert reused["action"] == "reuse_report"
        with patch.object(iris, "tool_info", side_effect=lambda name: missing[name]), patch.object(
                scanners, "tool_info", side_effect=lambda name: missing[name]):
            waiting = invoke("prepare", "--project", project, "--tools", "gitleaks")
        waiting_review = Path(waiting["review"])
        invoke('render', '--review', waiting_review)
        invoke("finish", "--review", waiting_review)
        with patch.object(iris, "tool_info", side_effect=lambda name: info if name == "gitleaks" else missing[name]):
            current = invoke("status", "--project", project)
            assert all(item["review"] != str(waiting_review) for item in current["reusable_reports"])
        external = kit / '.local/exports/informe-exportado.html'
        invoke("export", "--review", review, "--output", external)
        assert storage.inventory(project)["identity"] == source["identity"]
        assert external.read_bytes() == report.read_bytes()
        report.write_text(report.read_text(encoding="utf-8") + "<p>Cambio</p>", encoding="utf-8")
        with patch.object(iris, "tool_info", side_effect=lambda name: missing[name]):
            current = invoke("status", "--project", project)
            assert all(item["review"] != str(review) for item in current["reusable_reports"])

        calls = []

        def scan(command, **kwargs):
            calls.append(command)
            output = Path(command[command.index("--report-path") + 1])
            output.write_text('[{"Secret":"ficticio","File":"app.py","RuleID":"fixture"}]', encoding="utf-8")
            return subprocess.CompletedProcess(command, 1, b"scan finished", b"")

        with patch.object(scanners, "tool_info", return_value=info), patch.object(scanners.subprocess, "run", side_effect=scan):
            generated = scanners.run_tool("gitleaks", source)
            assert generated["status"] == "complete" and generated["cache"] == "generated"
            second = scanners.run_tool("gitleaks", source)
            assert second["cache"] == "reused" and len(calls) == 1
            raw = Path(generated["folder"]) / "resultado.json"
            assert "ficticio" not in raw.read_text(encoding="utf-8")
            raw.write_text("[]", encoding="utf-8")
            repaired = scanners.run_tool("gitleaks", source)
            assert repaired["status"] == "complete" and repaired["folder"] != generated["folder"]
            assert scanners.run_tool("gitleaks", source)["cache"] == "reused"
        with patch.object(scanners, "tool_info", return_value=info):
            assert scanners.run_tool("osv", source)["status"] == "needs_network_consent"
        assert code.read_text(encoding="utf-8") == "def hola():\n    return 'hola'\n"
    print("Verificados cambios locales, ramas, commits, entradas por herramienta, reutilización, publicación, exportación, integridad y reparación de caché.")


if __name__ == "__main__":
    main()
