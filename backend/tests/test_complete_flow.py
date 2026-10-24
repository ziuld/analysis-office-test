import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from arktic_office.preparation.snapshot import acquire_complete, snapshot_workspace
from arktic_office.preparation.evidence import Evidence, prepare_complete
from arktic_office.preparation.repository import AuditError
from arktic_office.coordination.team import run_team, prepare_partial_response
from test_team import snapshot, fake_invoke


class CompleteFlowTests(unittest.TestCase):
    def fixture(self, missing=False, lfs=False):
        files = {".hidden.py": b"value = 1", "tests/test_app.py": b"assert True", "asset.bin": b"a\0b"}
        if lfs:
            files["large.dat"] = b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 42\n"
        tree = [{"path": p, "type": "blob", "mode": "100644", "size": len(b), "sha": hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()} for p, b in files.items()]
        def fetch(path):
            if "recursive" in path: return {"tree": tree, "truncated": False}
            if "/branches/" in path: return {"commit": {"sha": "a" * 40, "commit": {"tree": {"sha": "b" * 40}}}}
            return {"default_branch": "main"}
        def download(owner, repo, commit, destination, limit, seconds):
            with tarfile.open(destination, "w:gz") as tar:
                for i, (p, b) in enumerate(files.items()):
                    if missing and i == 0: continue
                    item = tarfile.TarInfo("repo/" + p); item.size = len(b)
                    tar.addfile(item, io.BytesIO(b))
        return fetch, download

    def test_full_snapshot_and_closed_failures(self):
        for missing, lfs in ((False, False), (True, False), (False, True)):
            fetch, downloader = self.fixture(missing, lfs)
            with tempfile.TemporaryDirectory() as temp:
                if missing or lfs:
                    with self.assertRaises(AuditError):
                        acquire_complete("https://github.com/acme/app", Path(temp), fetch=fetch, downloader=downloader)
                else:
                    result = acquire_complete("https://github.com/acme/app", Path(temp), fetch=fetch, downloader=downloader)
                    self.assertEqual(result["tree_files"], 3)
                    self.assertEqual(len(result["inventory"]), 3)
                    self.assertEqual(result["files"][2]["kind"], "binary")
                self.assertFalse((Path(temp) / "snapshot.tar.gz").exists())
            self.assertFalse(Path(temp).exists())

    def test_lookup_preserves_original_lines_and_isolation(self):
        evidence = Evidence([{"path": "test.py", "text": "\n".join(["padding"] * 30 + ["target = 1"])}], {"nodes": [], "edges": []})
        result = evidence.lookup({"query": "target", "paths": ["test.py"]})
        self.assertEqual(result["fragments"][0]["text"].splitlines()[30], "target = 1")
        with self.assertRaises(AuditError): evidence.lookup({"paths": ["../other.py"]})
        mixed = evidence.lookup({"paths": ["test.py", "missing.py"]})
        self.assertEqual(mixed["unavailable_paths"], ["missing.py"])
        self.assertEqual([f["path"] for f in mixed["fragments"]], ["test.py"])
        failure = evidence.respond({"query": "x" * 121})
        self.assertIn("error", failure)
        self.assertEqual(failure["fragments"], [])

    def test_invalid_finding_does_not_discard_valid_one(self):
        value = snapshot(); cell = {"id": "inventory", "name": "Inventory", "files": value["files"]}
        raw = json.loads(fake_invoke("", cell)["report"])
        raw["confirmados"].append({**raw["confirmados"][0], "evidencia": ["F999:L1"]})
        report, _, warnings = prepare_partial_response(json.dumps(raw), value, "inventory")
        self.assertEqual(len(report["confirmados"]), 1)
        self.assertTrue(warnings)

    def test_specialists_choose_sources_with_bounded_rounds(self):
        for budget, fail_extra in ((0, False), (1, False), (2, False), (1, True)):
            value = snapshot(); value["request"] = {"mode": "ai", "capabilities": []}
            evidence = Evidence(value["files"] + [{"path": "hidden/entry.py", "text": "start = True"}], {"nodes": [], "edges": []})
            calls = []
            def invoke(prompt, config):
                role = config["id"]
                calls.append(role)
                if role == "coordinator-routing":
                    self.assertNotIn("source_samples", prompt)
                    return {"report": json.dumps({r: "Review your specialty" for r in ("security", "architecture", "inventory")})}
                if role == "coordinator-synthesis":
                    return {"report": json.dumps({"resumen": [{"texto": "Architecture observation", "aportaciones": ["architecture:confirmados:0"]}]})}
                if budget and calls.count(role) == 1:
                    self.assertEqual(config["files"], [])
                    return {"report": json.dumps({"queries": [{"paths": ["hidden/entry.py"]}]}), "usage": {"total_tokens": 1}}
                if fail_extra and role == "security":
                    raise AuditError("Controlled analysis failure")
                if budget == 2 and calls.count(role) == 2:
                    return {"report": json.dumps({"queries": [{"paths": ["auth.py"]}]}), "usage": {"total_tokens": 1}}
                if not budget:
                    return {"report": json.dumps({"schema_version": 3, "confirmados": [], "indicios": [], "dudas": ["No source budget"], "controles": []})}
                self.assertIn("hidden/entry.py", [f["path"] for f in config["files"]])
                return fake_invoke(prompt, config)
            env = {"AUDIT_" + role + "_RESEARCH_ROUNDS": str(budget) for role in ("SECURITY", "ARCHITECTURE", "INVENTORY")}
            with patch.dict(os.environ, env), tempfile.TemporaryDirectory() as temp:
                report = run_team(value, Path(temp), invoke=invoke, evidence=evidence, emit=lambda *a, **k: None)
                cells = {c["id"]: c for c in report["celulas"]}
                self.assertEqual(cells["inventory"]["calls"], 1 + budget)
                self.assertEqual(cells["inventory"]["execution"], "completed")
                self.assertEqual(cells["security"]["execution"], "error" if fail_extra else "completed")
                if budget and not fail_extra:
                    self.assertEqual(cells["security"]["usage"]["total_tokens"], 50 + budget)
                if fail_extra:
                    self.assertIsNone(cells["security"]["usage"])
                    self.assertEqual(cells["security"]["invocations"][0]["usage"]["total_tokens"], 1)

    def test_processing_failure_prevents_model_stage(self):
        fetch, downloader = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(AuditError):
                prepare_complete("https://github.com/acme/app", Path(temp), fetch=fetch, downloader=downloader,
                                 index=lambda *a, **k: {"status": "error"})

    def test_interrupted_workspace_is_recovered_and_normal_exit_cleans(self):
        with snapshot_workspace() as first:
            root = first.parent
            abandoned = root / "job-abandoned"
            abandoned.mkdir()
            (abandoned / "raw.txt").write_text("temporary")
        self.assertFalse(first.exists())
        with snapshot_workspace() as second:
            self.assertFalse(abandoned.exists())
            self.assertTrue(second.exists())
        self.assertFalse(second.exists())

    def test_research_batch_safety_lines_and_caps(self):
        evidence = Evidence([{"path": "app.py", "text": "\n".join(["padding"] * 110 + ["target = 1"])}], {"nodes": [], "edges": []})
        files, trace = evidence.batch([{"paths": ["../escape.py"]}, {"paths": ["app.py"], "start_line": 105}], {"files": 1, "bytes": 12000})
        self.assertIn("error", trace[0]["result"])
        self.assertEqual(files[0]["text"].splitlines()[110], "target = 1")
        self.assertEqual(files[0]["start"], 105)
        with self.assertRaises(AuditError):
            evidence.batch([{}] * 5, {"files": 1, "bytes": 12000})
        files, trace = evidence.batch([{"paths": ["app.py"]}], {"files": 0, "bytes": 0})
        self.assertEqual(files, [])
        self.assertEqual(trace[0]["result"]["omitted_by_budget"], ["app.py"])
        initial = [{"path": "app.py", "text": "padding"}]
        files, trace = evidence.batch([{"paths": ["app.py"], "start_line": 105}], {"files": 1, "bytes": 100}, initial=initial)
        self.assertEqual(files, initial)
        self.assertEqual(trace[0]["result"]["omitted_by_budget"], ["app.py"])


    def test_bad_presentation_is_reported_once_without_discarding_core(self):
        value = snapshot()
        cell = {"id": "architecture", "name": "Architecture", "files": value["files"]}
        data = json.loads(fake_invoke("", cell)["report"])
        data["confirmados"] *= 2
        data["presentacion"] = {"flujo_actual": {"componentes": [{"id": "invalid-id", "nombre": "API", "descripcion": "Entry", "evidencia": ["F1:L1"]}], "conexiones": []}}
        report, _, warnings = prepare_partial_response(json.dumps(data), value, "architecture")
        self.assertEqual(len(report["confirmados"]), 2)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Identificador de flujo", warnings[0])
        self.assertNotIn("flujo_actual", report.get("presentacion", {}))
