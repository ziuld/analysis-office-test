"""Two bounded regressions using the installed Graphify; no models or target execution."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ExtractionCoverageTests(unittest.TestCase):
    def extract(self, files):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'source'
            root.mkdir()
            for name, content in files.items():
                (root / name).write_text(content, encoding='utf-8')
            output = Path(temp) / 'graph.json'
            completed = subprocess.run([sys.executable, str(Path(__file__).with_name('extract_complete.py')), str(root), str(output)], cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
            return json.loads(output.read_text(encoding='utf-8'))

    def test_native_json_data_exclusions_are_counted_without_fake_ast_coverage(self):
        result = self.extract({'package.json':'{"dependencies":{"react":"18.2.0"}}', 'data.json':'[{"value":1}]', 'package-lock.json':'{"lockfileVersion":3,"packages":{}}'})
        self.assertTrue(result['processing_complete'])
        coverage = {x['path']:x for x in result['file_coverage']}
        self.assertEqual(coverage['package.json']['status'],'processed')
        self.assertEqual(coverage['data.json']['status'],'unsupported')
        self.assertEqual(coverage['package-lock.json']['reason'],'unsupported_json_data_schema')
        self.assertEqual(len(coverage),3)

    def test_real_json_capacity_error_still_blocks_extraction(self):
        result = self.extract({'large.json':' ' * 1_048_577})
        self.assertFalse(result['processing_complete'])
        self.assertEqual(result['file_coverage'][0]['status'],'error')
