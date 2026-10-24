"""Safety regressions for archive materialization; no target code is executed."""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from runner import unpack


class SnapshotTests(unittest.TestCase):
    def archive(self, root, name="repo/code.py", kind=None, content=b"pass\n"):
        path = root / "source.tar.gz"
        with tarfile.open(path, "w:gz") as tar:
            info = tarfile.TarInfo(name)
            info.size = len(content)
            if kind:
                info.type = kind
                info.linkname = "/etc/passwd"
                info.size = 0
            tar.addfile(info, io.BytesIO(content))
        return path

    def test_rejects_traversal_and_absolute_paths(self):
        for name in ("repo/../../escape.py", "/repo/escape.py", "repo/back\\slash.py"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with self.assertRaises(ValueError):
                    unpack(self.archive(root, name), root / "snapshot")
                self.assertFalse((root / "escape.py").exists())

    def test_does_not_follow_archive_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = unpack(self.archive(root, kind=tarfile.SYMTYPE), root / "snapshot")
            self.assertEqual(result["files"], 0)
            self.assertEqual(result["skipped"][0]["reason"], "not_regular_file")

    def test_excludes_secrets_and_generated_directories(self):
        for name in ("repo/.env", "repo/vendor/code.py", "repo/node_modules/code.js"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                result = unpack(self.archive(root, name), root / "snapshot")
                self.assertEqual(result["files"], 0)

    def test_enforces_total_budget_and_preserves_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.archive(root)
            with patch.dict("runner.LIMITS", snapshot_bytes=1):
                with self.assertRaises(ValueError):
                    unpack(archive, root / "snapshot")
            with self.assertRaises(ValueError):
                unpack(archive, root / "snapshot")

    def test_expansion_budget_applies_even_to_excluded_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.archive(root, "repo/vendor/ignored.py")
            with patch.dict("runner.LIMITS", snapshot_bytes=1):
                with self.assertRaisesRegex(ValueError, "expansion"):
                    unpack(archive, root / "snapshot")


if __name__ == "__main__":
    unittest.main()
