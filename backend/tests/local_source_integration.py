import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from arktic_office.core.errors import AuditError
from arktic_office.preparation.local import acquire_local
from arktic_office.reporting.brief import references

spec = importlib.util.spec_from_file_location('export_local', Path(__file__).resolve().parents[2]/'scripts/export-local.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class LocalSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root/'repo'
        self.repo.mkdir()
        self.git('init','-b','feature/actual')
        self.git('config','user.name','Fixture')
        self.git('config','user.email','fixture@example.invalid')
        (self.repo/'app.vue').write_bytes(b'<script>const n = 1;</script>\r\n')
        (self.repo/'.gitattributes').write_text('app.vue export-ignore\n')
        self.git('add','.')
        self.git('commit','-m','Fixture')

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL).decode().strip()

    def bundle(self):
        target = self.root/'bundle'
        exporter.export(self.repo,target,origin=r'C:\Work\Mi%20web')
        return target

    def workspace(self):
        path=self.root/'workspace';path.mkdir();return path

    def test_active_branch_and_canonical_bytes_even_export_ignored(self):
        bundle=self.bundle()
        snapshot=acquire_local(bundle,self.workspace())
        self.assertEqual(snapshot['branch'],'feature/actual')
        self.assertEqual(snapshot['commit'],self.git('rev-parse','HEAD'))
        self.assertEqual(snapshot['repository'],'local:///Mi%2520web')
        self.assertEqual(snapshot['project_name'],'Mi web')
        self.assertEqual(snapshot['tree_files'],2)
        self.assertEqual((self.root/'workspace/source/app.vue').read_bytes(),b'<script>const n = 1;</script>\r\n')
        self.assertEqual(self.git('branch','--show-current'),'feature/actual')
        self.assertEqual(self.git('status','--porcelain'),'')
        self.assertEqual(references({'evidencia':[{'path':'app.vue','line':1}]},snapshot),'app.vue:1')

    def test_dirty_checkout_rejected_without_silent_omissions(self):
        (self.repo/'app.vue').write_text('modified')
        with self.assertRaisesRegex(ValueError,'cambios locales'): self.bundle()

    def test_untracked_file_rejected(self):
        (self.repo/'extra.txt').write_text('untracked')
        with self.assertRaisesRegex(ValueError,'sin seguimiento'): self.bundle()

    def test_custom_git_filter_rejected_before_status_can_execute_it(self):
        self.git('config','filter.custom.clean','touch should-never-exist')
        with self.assertRaisesRegex(ValueError,'Filtros Git personalizados'): self.bundle()
        self.assertFalse((self.repo/'should-never-exist').exists())

    def test_detached_head_recorded_without_branch_guess(self):
        self.git('checkout','--detach')
        meta=exporter.export(self.repo,self.root/'bundle')
        self.assertEqual(meta['branch'],'HEAD')
        self.assertTrue(meta['detached_head'])

    def test_windows_crlf_configuration_does_not_report_false_dirty(self):
        self.git('config','core.autocrlf','true')
        (self.repo/'app.vue').write_bytes(b'<script>const n = 1;</script>\n')
        (self.repo/'notes.txt').write_bytes(b'line\n')
        self.git('add','.'); self.git('commit','-m','notes')
        (self.repo/'notes.txt').unlink()
        self.git('checkout-index','-u','-f','-a')
        self.assertEqual((self.repo/'notes.txt').read_bytes(),b'line\r\n')
        meta=exporter.export(self.repo,self.root/'bundle',autocrlf='true',filemode='false')
        self.assertFalse(meta['dirty'])
        self.assertEqual((self.root/'bundle/source/notes.txt').read_bytes(),b'line\n')

    def test_tampered_content_rejected(self):
        bundle=self.bundle()
        (bundle/'source/app.vue').write_text('tampered')
        with self.assertRaises(AuditError): acquire_local(bundle,self.workspace())

    def test_traversal_rejected(self):
        bundle=self.bundle()
        meta=json.loads((bundle/'snapshot.json').read_text())
        meta['files'][0]['path']='../escape'
        (bundle/'snapshot.json').write_text(json.dumps(meta))
        with self.assertRaises(AuditError): acquire_local(bundle,self.workspace())

    def test_symlink_cannot_read_outside_bundle(self):
        bundle=self.bundle()
        target=bundle/'source/app.vue'
        target.unlink()
        target.symlink_to(self.repo/'app.vue')
        with self.assertRaises(AuditError): acquire_local(bundle,self.workspace())

    def test_submodule_not_silently_skipped(self):
        (self.repo/'external').mkdir()
        self.git('update-index','--add','--cacheinfo','160000,'+self.git('rev-parse','HEAD')+',external')
        self.git('commit','-m','gitlink')
        with self.assertRaisesRegex(ValueError,'Submódulo'): self.bundle()


if __name__=='__main__': unittest.main()
