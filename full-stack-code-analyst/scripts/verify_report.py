"""Regression tests: stable layout, permission denial and no external-workspace fallback."""
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.dont_write_bytecode = True


def main():
    original = Path(__file__).resolve().parents[1]
    qa = original / '.local/qa'
    qa.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=qa, prefix='report-') as temp:
        project = Path(temp)
        kit = project / 'iris'
        shutil.copytree(original, kit, ignore=shutil.ignore_patterns('.local','__pycache__','*.pyc'))
        subprocess.run(['git','init','-q',str(project)], capture_output=True, check=True)
        (project / 'app.py').write_text('print("fixture")\n', encoding='utf8')
        sys.path.insert(0, str(kit / 'scripts'))
        import iris
        import storage
        import report_renderer
        import argparse
        def rejected(fn):
            try:
                fn()
            except ValueError:
                return
            raise AssertionError('Debía rechazarse')
        tools = {k:{'status':'missing'} for k in iris.VERSIONS}
        args = argparse.Namespace(tools='',refresh='',online=False,force_review=False,interpretation='deep',mode='new',
                                  base_review=None,fresh_context=False,semgrep_engine='local',allow_image_download=False)
        prepared = iris.prepare(args, storage.inventory(project), tools)
        review = Path(prepared['review'])
        state = storage.read_json(review / 'estado.json')
        data = storage.read_json(review / 'informe.json')
        data['answers']['Q04']['text'] = '<script>alert("untrusted")</script> & <b>texto</b>'
        data['answers']['Q04']['sources'] = ['app.py:1']
        storage.write_json(review / 'informe.json', data)
        html = report_renderer.render(review, state)
        assert '&lt;script&gt;' in html and '<script>alert' not in html
        assert html.count('class="question-id"') == 40
        assert html.count('class="reading-answer"') == 40
        assert len(re.findall(r'<h4>', html)) == 40
        for name in ('resumen-aplicacion','resumen-prioridades','resumen-protecciones','resumen-limites'):
            assert f'id="{name}"' in html
        template = (kit / 'plantillas/informe.html').read_text(encoding='utf8')
        assert re.findall(r'<style>(.*?)</style>',html,re.S) == re.findall(r'<style>(.*?)</style>',template,re.S)
        assert iris.validate_report(review / 'informe-iris.html', state['source'])['questions'] == 40
        # This used to pass: same CSS and IDs, but missing card layout.
        broken = html.replace('class="panel reading-panel"', 'class="bare"')
        storage.atomic_text(review / 'informe-iris.html', broken)
        rejected(lambda: iris.finish(argparse.Namespace(review=str(review), author='fixture', coverage='partial')))
        storage.atomic_text(review / 'informe-iris.html', html)
        iris.finish(argparse.Namespace(review=str(review), author='fixture', coverage='partial'))
        rejected(lambda: storage.atomic_text(project / 'informe-fuera.html', 'No debe escribirse'))
        rejected(lambda: storage.local_path(project / 'informe-fuera.html'))
        assert not (project / 'informe-fuera.html').exists()
        other = project / 'otro-proyecto'
        other.mkdir()
        with patch.object(sys,'argv',['iris.py','status','--project',str(other)]), \
             patch.object(iris,'locked') as lock, redirect_stderr(StringIO()) as stderr:
            assert iris.main() == 1
            lock.assert_not_called()
            assert 'instalada dentro del proyecto' in stderr.getvalue()
        original_open = Path.open
        def denied(path, *args, **kwargs):
            if path == kit / '.local/iris.lock':
                raise PermissionError('Fixture: permiso denegado')
            return original_open(path, *args, **kwargs)
        with patch.object(sys,'argv',['iris.py','status','--project',str(project)]), \
             patch.object(Path,'open',denied), redirect_stderr(StringIO()) as stderr:
            assert iris.main() == 1
            error = json.loads(stderr.getvalue())
            assert error['error_code'] == 'permission_required'
            assert error['fallback_allowed'] is False and error['required_path'] == str(kit / '.local')
        assert not (project / 'outputs').exists()
    print('Verificados formato fijo, 40 etiquetas/h4, cuatro grupos, escape HTML, rechazo de edición manual, destino interno y error de permisos sin alternativa.')


if __name__ == '__main__':
    main()
