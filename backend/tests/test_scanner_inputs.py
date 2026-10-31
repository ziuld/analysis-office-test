import json
import unittest
from pathlib import Path
from arktic_office.adapters.scanners import scan, osv_input

class ScannerInputTests(unittest.TestCase):
    def test_polyglot_detection_and_boms_without_preselecting_language(self):
        names = ["api/requirements-dev.txt", "Pipfile.lock", "uv.lock", "java/pom.xml", "java/gradle.lockfile", "frontend/package-lock.json", "bun.lock", "app.deps.json", "packages.lock.json", "go.mod", "bom.json", "audit.spdx.json"]
        self.assertTrue(all(osv_input(p) for p in names))
        self.assertIsNone(osv_input("app.py"))
        self.assertIsNone(osv_input("package.json"))
        def runner(cmd, out):
            if cmd[0] == "gitleaks": return []
            self.assertEqual(cmd[0], "osv-scanner")
            self.assertNotIn("--no-resolve", cmd)
            self.assertEqual(sum(a.startswith("--sbom=") for a in cmd), 2)
            self.assertTrue(any(a.startswith("--lockfile=requirements.txt:") for a in cmd))
            return {"results": []}
        result = scan([{"path": p, "text": "{}"} for p in names], runner)
        self.assertEqual(set(result[1]["input_files"]), set(names))
        self.assertEqual(result[1]["status"], "no_evaluado")

    def test_sast_keeps_locations_but_never_raw_code_or_messages(self):
        def runner(cmd, out):
            if cmd[0] == "gitleaks": return []
            self.assertEqual(cmd[0], "semgrep")
            source = out.parent / "sast-source" / "app.py"
            self.assertIn("--metrics=off", cmd)
            self.assertEqual((source.parent / ".semgrepignore").read_text(), "")
            return {"results": [{"path": str(source), "start": {"line": 1}, "check_id": "arktic.python-dynamic-execution", "extra": {"message": "DO NOT RETAIN", "lines": "PRIVATE CODE"}}], "paths": {"scanned": [str(source)]}, "errors": []}
        result = scan([{"path": "app.py", "text": "eval(user_input)"}], runner)[2]
        self.assertEqual(result["status"], "detecciones_por_validar")
        self.assertEqual(result["findings"][0]["line"], 1)
        self.assertNotIn("PRIVATE CODE", json.dumps(result))
        self.assertNotIn("DO NOT RETAIN", json.dumps(result))

    def test_sast_partial_scan_is_not_a_pass(self):
        def runner(cmd, out):
            return [] if cmd[0] == "gitleaks" else {"results": [], "paths": {"scanned": []}, "errors": []}
        self.assertEqual(scan([{"path": "app.py", "text": "x = 1"}], runner)[2]["status"], "error")

    def test_new_php_and_go_rules_receive_their_source_files(self):
        def runner(cmd, out):
            if cmd[0] == 'gitleaks':
                return []
            self.assertEqual(cmd[0], 'semgrep')
            source = out.parent/'sast-source'
            paths = [str(source/'app.php'), str(source/'main.go')]
            self.assertTrue(all(Path(p).is_file() for p in paths))
            return {'results':[], 'paths':{'scanned':paths}, 'errors':[]}
        result = scan([{'path':'app.php','text':'<?php echo 1;'}, {'path':'main.go','text':'package main'}], runner)[2]
        self.assertEqual(set(result['input_files']), {'app.php','main.go'})
        self.assertEqual(result['status'], 'sin_detecciones_en_seleccion')
