"""Real opt-in Docker smoke test against a tiny synthetic project, never user code."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-image-download', action='store_true')
    args = parser.parse_args()
    original = Path(__file__).resolve().parents[1]
    project = original / '.local/qa' / ('docker-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:6])
    kit = project / 'iris'
    shutil.copytree(original, kit, ignore=shutil.ignore_patterns('.local', '__pycache__', '*.pyc'))
    subprocess.run(['git', 'init', '-q', str(project)], check=True, capture_output=True)
    fixture = project / 'app.py'
    text = 'def run(user_input):\n    return eval(user_input)\n'
    fixture.write_text(text, encoding='utf8')
    sys.path.insert(0, str(kit / 'scripts'))
    import scanners
    import storage
    source = storage.inventory(project)
    result = scanners.run_tool('semgrep', source, semgrep_engine='docker', allow_image_download=args.allow_image_download)
    storage.write_json(kit / '.local/verificacion.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    assert result['status'] == 'complete', 'La prueba real no terminó; consulta el estado y el log local.'
    payload = storage.read_json(Path(result['folder']) / 'resultado.json')
    assert any(r['check_id'] == 'arktic.python-dynamic-execution' for r in payload['results'])
    assert all(r['path'] == 'app.py' for r in payload['results'])
    assert payload['version'] == result['version']
    reused = scanners.run_tool('semgrep', source, semgrep_engine='docker')
    assert reused['cache'] == 'reused' and reused['key'] == result['key']
    assert fixture.read_text(encoding='utf8') == text
    print('Prueba real correcta: patrón detectado, copia original intacta, contenedor eliminado y caché reutilizada.')


if __name__ == '__main__':
    main()
