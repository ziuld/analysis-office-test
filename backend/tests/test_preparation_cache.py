import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from arktic_office.preparation.evidence import prepare_complete
from arktic_office.core.errors import AuditError


class PreparationCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.acquired = {'repository': 'https://github.com/acme/app', 'commit': 'a' * 40, 'branch': 'main',
            'files': [{'path': 'app.py', 'text': 'print(1)', 'kind': 'text'}],
            'inventory': [{'path': 'app.py', 'kind': 'text', 'bytes': 8, 'git_blob': 'b' * 40}],
            'acquisition_complete': True, 'tree_files': 1, 'excluded': []}
        self.calls = {'scan': 0, 'index': 0}
        self.signature = 'index-v1'

    def prepare(self, *, refresh=False, broken=False):
        artifacts = self.root / ('run-' + str(len(list(self.root.glob('run-*')))))
        artifacts.mkdir()
        def scan(files, **kwargs):
            self.calls['scan'] += 1
            (artifacts / 'scanner.json').write_text('{"findings": []}')
            return []
        def index(files, **kwargs):
            self.calls['index'] += 1
            return {'status': 'error' if broken else 'ready', 'processing_complete': not broken,
                    'nodes': [], 'edges': [], 'file_coverage': [{'path': 'app.py', 'status': 'processed'}]}
        with patch('arktic_office.preparation.snapshot.acquire_complete'):
            with patch('arktic_office.preparation.evidence.acquire_complete', return_value=copy.deepcopy(self.acquired)):
                snapshot, evidence = prepare_complete('url', self.root, scanner=scan, index=index,
                    artifact_directory=artifacts, cache_root=self.root / '.cache',
                    indexer_signature=self.signature, refresh=refresh)
        return snapshot, evidence, artifacts

    def test_models_and_prompts_do_not_repeat_scanners_or_graph_and_artifacts_are_preserved(self):
        first, evidence, _ = self.prepare()
        with patch.dict(os.environ, {'AUDIT_MODEL': 'another-model', 'AUDIT_REASONING': 'high'}):
            second, restored, artifacts = self.prepare()
        self.assertEqual(self.calls, {'scan': 1, 'index': 1})
        self.assertEqual(second['preparation']['cache']['status'], 'reused')
        self.assertEqual(second['preparation']['cache']['key'], first['preparation']['cache']['key'])
        self.assertEqual(evidence.files, restored.files)
        self.assertTrue((artifacts / 'scanner.json').is_file())

    def test_commit_repository_and_tool_changes_invalidate(self):
        self.prepare()
        self.acquired['commit'] = 'c' * 40
        self.prepare()
        self.acquired['repository'] = 'https://github.com/acme/other'
        self.prepare()
        self.signature = 'index-v2'
        self.prepare()
        self.assertEqual(self.calls, {'scan': 4, 'index': 4})

    def test_corruption_and_manual_refresh_regenerate_instead_of_using_invalid_data(self):
        snapshot, _, _ = self.prepare()
        entry = self.root / '.cache' / snapshot['preparation']['cache']['key']
        (entry / 'payload.json').write_text('{}')
        self.prepare()
        self.prepare(refresh=True)
        self.assertEqual(self.calls, {'scan': 3, 'index': 3})

    def test_failed_preparation_is_never_cached(self):
        with self.assertRaises(AuditError):
            self.prepare(broken=True)
        self.prepare()
        self.assertEqual(self.calls, {'scan': 2, 'index': 2})
        self.assertEqual(len(list((self.root / '.cache').glob('[!.]*'))), 1)
