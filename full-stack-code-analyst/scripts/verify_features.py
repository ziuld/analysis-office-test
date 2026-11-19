"""Offline checks for provenance, dependency triage and container execution failures."""
import argparse
from pathlib import Path
import json
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
    with TemporaryDirectory(dir=qa, prefix='features-') as temp:
        project = Path(temp)
        kit = project / 'iris'
        shutil.copytree(original, kit, ignore=shutil.ignore_patterns('.local', '__pycache__', '*.pyc'))
        sys.path.insert(0, str(kit / 'scripts'))
        import iris
        import scanners
        import storage
        import review_evidence as evidence
        import semgrep_docker as docker
        subprocess.run(['git', 'init', '-q', str(project)], check=True, capture_output=True)
        (project / 'app.py').write_text('print("fixture")\n', encoding='utf8')
        source = storage.inventory(project)
        report = project / 'informe-anterior.html'
        report.write_text('Hallazgos anteriores que no deben orientar la prueba', encoding='utf8')
        scoped = storage.inventory(project, ['informe-anterior.html'])
        assert next(x for x in scoped['files'] if x['path'] == report.name)['kind'] == 'excluded_scope'
        assert all(x['path'] != report.name for x in scanners.selected_files('graphify', scoped))
        report.unlink()
        tools = {name: {'status': 'missing'} for name in scanners.VERSIONS}
        def args(**overrides):
            values = dict(tools='', refresh='', online=False, force_review=False, interpretation='deep',
                          mode='new', base_review=None, fresh_context=False, semgrep_engine='local', allow_image_download=False)
            return argparse.Namespace(**(values | overrides))
        def raises(fn):
            try:
                fn()
            except ValueError:
                return
            raise AssertionError('La operación debía rechazarse')
        raises(lambda: storage.inventory(project, ['../fuera']))
        def finish(folder):
            iris.report_renderer.render(folder, storage.read_json(folder / 'estado.json'))
            return iris.finish(argparse.Namespace(review=str(folder), author='fixture', coverage='partial'))
        prepared = iris.prepare(args(), source, tools)
        base = Path(prepared['review'])
        assert prepared['provenance']['mode'] == 'new'
        finding = dict(key='risk-a', id='R01', block=1, title='<script>untrusted</script>', severity='Media', certainty='Indicio',
                       status='open', sources=['app.py:1'], verification='Pendiente de prueba', observation='Patrón',
                       effect='Impacto condicionado', conditions='Configuración pendiente', action='Verificar')
        storage.write_json(base / 'hallazgos.json', [finding, finding | dict(key='risk-b', id='R02')])
        finish(base)
        raises(lambda: iris.finish(argparse.Namespace(review=str(base), author='fixture', coverage='complete')))
        assert iris.prepare(args(), source, tools)['action'] == 'reuse_report'
        extension = iris.prepare(args(mode='extend', base_review=str(base)), source, tools)
        folder = Path(extension['review'])
        assert folder != base
        state = storage.read_json(folder / 'estado.json')
        storage.write_json(folder / 'hallazgos.json', [finding | dict(status='resolved')])
        raises(lambda: evidence.render(folder, state))
        storage.write_json(folder / 'hallazgos.json', [finding | dict(status='resolved', resolution_evidence='app.py:1')])
        html = evidence.render(folder, state)
        assert '&lt;script&gt;' in html and '<script>untrusted' not in html
        changes = storage.read_json(folder / 'comparacion.json')
        assert {x['key']: x['change'] for x in changes} == {'risk-a': 'resuelto', 'risk-b': 'pendiente: no reevaluado'}
        finish(folder)
        raises(lambda: iris.prepare(args(mode='independent'), source, tools))
        independent = Path(iris.prepare(args(mode='independent', fresh_context=True), source, tools)['review'])
        state = storage.read_json(independent / 'estado.json')
        coverage = storage.read_json(independent / 'cobertura.json')
        coverage[0]['reused_sources'] = ['app.py:1']
        storage.write_json(independent / 'cobertura.json', coverage)
        raises(lambda: evidence.render(independent, state))
        coverage[0]['reused_sources'] = []
        storage.write_json(independent / 'cobertura.json', coverage)

        native = kit / '.local/cache/osv-fixture'
        native.mkdir(parents=True)
        storage.write_json(native / 'resultado.json', {'results': [{'packages': [{
            'package': {'name': 'fixture', 'version': '1.0.0', 'ecosystem': 'npm'},
            'vulnerabilities': [{'id': 'GHSA-fixture', 'summary': '<unsafe>', 'affected': [
                {'package': {'name': 'fixture'}, 'ranges': [{'events': [{'fixed': '1.1.0'}]}]}]}]}]}]})
        state['tools']['osv'] = {'status': 'complete', 'folder': str(native), 'cache': 'generated'}
        evidence.initialize(independent, state)
        rows = storage.read_json(independent / 'dependencias.json')
        assert rows[0]['fixed_versions'] == ['1.1.0']
        storage.write_json(independent / 'dependencias.json', [])
        raises(lambda: evidence.render(independent, state))
        rows[0]['decision'] = 'not_applicable'
        storage.write_json(independent / 'dependencias.json', rows)
        raises(lambda: evidence.render(independent, state))
        rows[0]['sources'] = ['app.py:1']
        storage.write_json(independent / 'dependencias.json', rows)
        assert '&lt;unsafe&gt;' in evidence.render(independent, state)

        docker_info = dict(status='available', engine='docker', version='1.182.1', executable='docker',
                           image=docker.image(), image_id='sha256:fixture')
        with patch.object(docker, 'info', return_value=docker_info | dict(status='needs_image_download', image_id=None)), \
             patch.object(docker, 'pull') as pull:
            assert scanners.run_tool('semgrep', source, semgrep_engine='docker')['status'] == 'needs_image_download'
            pull.assert_not_called()
        assert scanners.run_tool('semgrep', source, semgrep_engine='skip')['status'] == 'skipped'
        assert scanners.signature('semgrep', source, docker_info) != scanners.signature('semgrep', source, docker_info | dict(engine='local'))
        assert scanners.signature('semgrep', source, docker_info) != scanners.signature('semgrep', source, docker_info | dict(image_id='sha256:changed'))
        calls = []
        def execute(command, **kwargs):
            calls.append(command)
            assert '--network=none' in command and '--read-only' in command and '--cap-drop=ALL' in command
            assert not any('docker.sock' in s for s in command)
            mounts = [command[i+1] for i, s in enumerate(command) if s == '--mount']
            assert len(mounts) == 3 and sum(s.endswith('readonly') for s in mounts) == 2
            output = Path(kwargs['cwd']) / 'output/resultado.json'
            output.write_text('{"version":"1.182.1", "results": [], "errors": []}', encoding='utf8')
            return subprocess.CompletedProcess(command, 0, b'', b'')
        with patch.object(docker, 'info', return_value=docker_info), patch.object(docker, 'cleanup', return_value={'status':'removed'}) as clean, \
             patch.object(scanners.subprocess, 'run', side_effect=execute):
            result = scanners.run_tool('semgrep', source, semgrep_engine='docker')
            assert result['status'] == 'complete' and clean.call_count == 1
            assert scanners.run_tool('semgrep', source, semgrep_engine='docker')['cache'] == 'reused'
            assert len(calls) == 1
        with patch.object(docker, 'info', return_value=docker_info), patch.object(docker, 'cleanup', return_value={'status':'removed'}) as clean, \
             patch.object(scanners.subprocess, 'run', side_effect=subprocess.TimeoutExpired('docker', 600)):
            result = scanners.run_tool('semgrep', source, semgrep_engine='docker', refresh=True)
            assert result['status'] == 'error' and clean.call_count == 1
        with patch.object(docker, 'info', return_value=docker_info), patch.object(docker, 'cleanup', return_value={'status':'cleanup_failed'}), \
             patch.object(scanners.subprocess, 'run', side_effect=execute):
            assert scanners.run_tool('semgrep', source, semgrep_engine='docker', refresh=True)['status'] == 'error'
        with patch.object(docker.shutil, 'which', return_value='docker'), patch.dict(docker.os.environ, {'DOCKER_HOST':'tcp://remote:2375'}), \
             patch.object(docker.subprocess, 'run') as process:
            assert docker.probe()['reason'] == 'remote_docker_not_supported'
            process.assert_not_called()
    print('Verificados procedencia, independencia declarada, comparación, matriz OSV, escape HTML, consentimiento Docker, aislamiento, caché y limpieza tras fallos.')


if __name__ == '__main__':
    main()
