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

    def test_specialist_budget_and_justified_omission(self):
        for budget, fail_extra in ((0, False), (1, False), (1, True)):
            value = snapshot(); value["request"] = {"mode": "ai", "capabilities": []}
            evidence = Evidence(value["files"], {"nodes": [], "edges": []})
            calls = []
            def invoke(prompt, config):
                calls.append(config["id"])
                if config["id"] == "coordinator-routing":
                    decision = {role: {"decision": "execute", "paths": ["Dockerfile"], "reason": "Deployment present", "missing": []} for role in ("security", "architecture", "inventory")}
                    decision["inventory"] = {"decision": "omit", "paths": [], "reason": "No dependency manifest supplied", "missing": ["dependency manifest"]}
                    return {"report": json.dumps(decision)}
                if config["id"] == "security" and calls.count("security") == 1:
                    return {"report": json.dumps({"retrieve": {"paths": ["auth.py"]}}), "usage": {"total_tokens": 1}}
                if config["id"] == "security" and fail_extra:
                    raise AuditError("Controlled extra-call failure")
                if config["id"] == "coordinator-synthesis":
                    return {"report": json.dumps({"resumen": [{"texto": "Architecture observation", "aportaciones": ["architecture:confirmados:0"]}]})}
                return fake_invoke(prompt, config)
            with patch.dict(os.environ, {"AUDIT_SECURITY_MAX_EXTRA_QUERIES": str(budget)}, clear=False), tempfile.TemporaryDirectory() as temp:
                report = run_team(value, Path(temp), invoke=invoke, evidence=evidence, emit=lambda *a, **k: None)
                cells = {c["id"]: c for c in report["celulas"]}
                self.assertEqual(cells["inventory"]["estado"], "no_ejecutado")
                self.assertEqual(cells["inventory"]["calls"], 0)
                self.assertEqual(calls.count("security"), 1 + budget)
                self.assertEqual(cells["security"]["execution"], "completed" if budget and not fail_extra else "error")
                if budget and not fail_extra: self.assertEqual(cells["security"]["usage"]["total_tokens"], 51)
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

    def test_coordinator_can_use_only_one_extra_query(self):
        from arktic_office.coordination.coordinator import Coordinator
        from arktic_office.coordination.team import plan_cells
        value = snapshot()
        evidence = Evidence(value["files"], {"nodes": [], "edges": []})
        for budget in (0, 1):
            calls = []
            def invoke(prompt, config):
                calls.append(config["id"])
                if len(calls) == 1:
                    response = {"retrieve": {"paths": ["Dockerfile"]}}
                else:
                    response = {role: {"decision": "execute", "paths": ["Dockerfile"], "reason": "Deployment source", "missing": []} for role in ("security", "architecture", "inventory")}
                return {"report": json.dumps(response)}
            with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"AUDIT_COORDINATOR_MAX_EXTRA_QUERIES": str(budget)}):
                coordinator = Coordinator(value, Path(temp), invoke, evidence=evidence)
                plan = coordinator.route(plan_cells(value))
                self.assertEqual(len(calls), 1 + budget)
                self.assertEqual(bool(coordinator.state.get("routing_fallback")), not bool(budget))
