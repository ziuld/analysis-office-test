"""Minimal regressions for packaging, stored history and internal state events."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

from arktic_office.core.errors import AuditError
from arktic_office.execution.jobs import Jobs
from arktic_office.reporting.executive import render_html
from arktic_office.reporting.reports import make_prompt, markdown
from arktic_office.storage.jsonio import write_json
from arktic_office.storage.runs import RunStore
from test_questions import fixture


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class CompatibilityTests(unittest.TestCase):
    def test_installed_package_renders_three_historical_report_schemas(self):
        reference = json.loads((Path(__file__).parent / "fixtures/mvp-contracts.json").read_text())
        snapshot = reference["snapshot"]
        self.assertIn("SOLO", make_prompt(snapshot))
        self.assertEqual(len(reference["cases"]), 3)
        for case in reference["cases"]:
            with self.subTest(version=case["version"]):
                md = markdown(case["report"], snapshot, "test")
                html = render_html(case["report"], snapshot, "test")
                self.assertIn(snapshot["commit"], md)
                self.assertIn(snapshot["commit"], html)
                for section in ("confirmados", "indicios"):
                    for item in case["report"].get(section, []):
                        from html import escape
                        self.assertIn(escape(item["observacion"]), html)
                        self.assertIn(item["observacion"], md)
                        for ref in item['evidencia']:
                            self.assertIn(ref['path'], html)
                            self.assertIn(ref['path'], md)

    def test_ids_resolve_flat_and_nested_history_without_modifying_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flat = root / "flat-history"
            nested = root / "2026-10-23/2030-title/nested-history"
            nested.parent.mkdir(parents=True)
            fixture(flat)
            fixture(nested)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            store = RunStore(root)
            jobs = Jobs(root)
            self.assertEqual(store.resolve(flat.name), flat)
            self.assertEqual(jobs.directory(nested.name), nested)
            self.assertEqual({x["id"] for x in jobs.listing()}, {flat.name, nested.name})
            self.assertTrue(jobs.detail(nested.name)["historical"])
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})
            with self.assertRaises(AuditError):
                store.resolve("../outside")
            (root / "outside-link").symlink_to(root.parent, target_is_directory=True)
            with self.assertRaises(FileNotFoundError):
                store.resolve("outside-link")
            # Duplicate IDs cannot silently return an unrelated saved report.
            fixture(root / nested.name)
            with self.assertRaisesRegex(AuditError, "duplicado"):
                store.resolve(nested.name)

    def test_events_follow_saved_states_with_an_injected_runner(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = []

            def runner(run_id, _repository):
                write_json(jobs.directory(run_id) / "informe.json", {"estado": "completo"})
                return 0

            def sink(event):
                persisted = json.loads((jobs.directory(event.run_id) / "job.json").read_text())
                self.assertEqual(event.state, persisted["estado"])
                self.assertEqual(event.to_dict()["version"], 1)
                events.append(event.state)

            jobs = Jobs(root, runner=runner, event_sink=sink)
            job = jobs.start("https://github.com/acme/app")
            deadline = time.monotonic() + 3
            while len(events) < 3 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(events, ["preparando", "analizando", "completo"])
            self.assertEqual(jobs.detail(job["id"])["estado"], "completo")


if __name__ == "__main__":
    unittest.main()
