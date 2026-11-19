"""Optional Semgrep container backend. Never installs or starts Docker."""
import os
from pathlib import Path
import shutil
import subprocess
import uuid

from storage import KIT, LOCAL, protect, read_json


def image():
    return read_json(KIT / 'tools/versions.json')['semgrep']['image']


def probe():
    binary = shutil.which('docker')
    if not binary:
        return {'status': 'missing', 'reason': 'docker_not_installed'}
    try:
        endpoint = os.environ.get('DOCKER_HOST')
        if not endpoint:
            context = subprocess.run([binary, 'context', 'inspect', '--format',
                                      '{{.Endpoints.docker.Host}}'], capture_output=True, timeout=15)
            if context.returncode:
                return {'status': 'unavailable', 'reason': 'docker_context_unavailable'}
            endpoint = context.stdout.decode('utf8', 'replace').strip()
        if not endpoint.startswith(('unix://', 'npipe://')):
            return {'status': 'unavailable', 'reason': 'remote_docker_not_supported'}
        server = subprocess.run([binary, 'info', '--format', '{{.OSType}}'],
                                capture_output=True, timeout=15)
        if server.returncode or server.stdout.strip() != b'linux':
            return {'status': 'unavailable', 'reason': 'linux_engine_not_ready'}
        inspected = subprocess.run([binary, 'image', 'inspect', '--format', '{{.Id}}', image()],
                                   capture_output=True, timeout=15)
        image_id = inspected.stdout.decode('utf8', 'replace').strip()
        return {'status': 'available', 'executable': binary, 'image': image(),
                'image_id': image_id if inspected.returncode == 0 and image_id.startswith('sha256:') else None}
    except (OSError, subprocess.TimeoutExpired):
        return {'status': 'unavailable', 'reason': 'docker_probe_failed'}


def info():
    docker = probe()
    spec = read_json(KIT / 'tools/versions.json')['semgrep']
    return {**docker, 'engine': 'docker', 'version': spec['version'],
            'status': ('available' if docker.get('image_id') else 'needs_image_download')
                      if docker['status'] == 'available' else docker['status']}


def pull():
    current = probe()
    if current['status'] != 'available':
        return info()
    folder = LOCAL / 'cache/docker'
    folder.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run([current['executable'], 'pull', image()], capture_output=True, timeout=600)
        (folder / 'descarga.log').write_text(protect((result.stdout + result.stderr).decode('utf8', 'replace')),
                                             encoding='utf8')
        if result.returncode:
            return {'status': 'error', 'engine': 'docker', 'reason': 'image_download_failed'}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status': 'error', 'engine': 'docker', 'reason': protect(str(exc))}
    return info()


def command(current, folder):
    output = folder / 'output'
    output.mkdir()
    (folder / 'input/.semgrepignore').write_text('', encoding='utf8')
    uid = f'{os.getuid()}:{os.getgid()}' if hasattr(os, 'getuid') else '65532:65532'
    name = 'iris-semgrep-' + uuid.uuid4().hex
    args = [current['executable'], 'run', '--rm', '--pull=never', '--name', name,
            '--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--user', uid, '--cpus=2', '--memory=1g', '--pids-limit=128', '--ipc=none',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=268435456',
            '--env', 'HOME=/tmp', '--env', 'XDG_CACHE_HOME=/tmp/cache',
            '--env', 'SEMGREP_SEND_METRICS=off', '--env', 'SEMGREP_SETTINGS_FILE=/tmp/settings.yml',
            '--mount', f'type=bind,source={(folder / "input").resolve()},target=/src,readonly',
            '--mount', f'type=bind,source={(KIT / "tools/semgrep-rules.json").resolve()},target=/rules.json,readonly',
            '--mount', f'type=bind,source={output.resolve()},target=/output',
            '--workdir', '/src', '--entrypoint', 'semgrep', current['image_id'],
            'scan', '--oss-only', '--config', '/rules.json', '--json', '--output', '/output/resultado.json',
            '--metrics=off', '--disable-version-check', '--no-git-ignore', '--no-rewrite-rule-ids',
            '--jobs=2', '--timeout=10', '--max-target-bytes=2000000', '/src']
    return args, output / 'resultado.json', name


def cleanup(binary, name):
    try:
        result = subprocess.run([binary, 'rm', '--force', name], capture_output=True, timeout=20)
        message = (result.stdout + result.stderr).decode('utf8', 'replace')
        return {'status': 'removed' if result.returncode == 0 else
                ('already_removed' if 'No such container' in message else 'cleanup_failed')}
    except (OSError, subprocess.TimeoutExpired):
        return {'status': 'cleanup_failed'}
