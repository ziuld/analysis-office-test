"""Only persisted activity and bounded, isolated read-only history."""
import json
import tempfile
import unittest
from pathlib import Path
from arktic_office.execution.jobs import Jobs
from arktic_office.execution.activity import project
from arktic_office.storage.jsonio import write_json
from arktic_office.storage.runs import RunStore
from arktic_office.storage.manifest import write_manifest
from test_questions import fixture


class OfficeStorageTests(unittest.TestCase):
    def test_terminal_state_overrides_stale_work_and_history_is_scoped_bounded_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / "saved-review"
            fixture(directory)
            jobs = Jobs(root, answerer=lambda *a: self.fail("History must not invoke a model"))
            queries = directory / "consultas"
            queries.mkdir(exist_ok=True)
            for n in range(12):
                write_json(queries / f"q{n}.json", {"id": str(n), "run_id": directory.name, "agent": "security",
                    "created": f"2026-10-23T10:00:{n:02d}Z", "question": str(n), "estado": "completada"})
            before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
            history = jobs.history(directory.name, "security")["questions"]
            self.assertEqual([q["id"] for q in history], [str(n) for n in range(11, 1, -1)])
            self.assertEqual(jobs.history(directory.name, "inventory")["questions"], [])
            self.assertEqual(before, {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()})
            write_json(directory / "coordinacion.json", {"stages": {"synthesis": {"status": "running"}}})
            cells = [{"id": "security", "estado": "analizando"}]
            live = project(directory, {"estado": "analizando"}, cells)
            self.assertTrue(live["coordinator"]["meeting"])
            terminal = project(directory, {"estado": "informacion_insuficiente"}, cells)
            self.assertTrue(all(not a["working"] and not a["meeting"] for a in terminal.values()))

    def test_new_dated_layout_manifest_and_flat_history_remain_resolvable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root / "flat-history")
            original = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            store = RunStore(root)
            directory = store.create("new-review-id", repository="https://github.com/acme/app")
            self.assertEqual(len(directory.relative_to(root).parts), 3)
            write_json(directory / "job.json", {"id": directory.name, "estado": "preparando"})
            self.assertEqual(store.resolve(directory.name), directory)
            snapshot = {"repository": "https://github.com/acme/app", "commit": "a" * 40, "files": []}
            write_manifest(directory, snapshot)
            manifest = json.loads((directory / "manifest.json").read_text())
            self.assertEqual(manifest["backend_version"], "0.3.0")
            self.assertEqual(manifest["delivery"], "closed")
            self.assertIn("editorial/standard.md", manifest["resource_sha256"])
            self.assertEqual(original, {p: p.read_bytes() for p in original})
            guarded, outside = root / "guarded", root / "outside"
            guarded.mkdir()
            outside.mkdir()
            (guarded / directory.relative_to(root).parts[0]).symlink_to(outside, target_is_directory=True)
            from arktic_office.core.errors import AuditError
            with self.assertRaises(AuditError):
                RunStore(guarded).create("guarded-review", repository="https://github.com/acme/app")
            self.assertEqual(list(outside.iterdir()), [])
