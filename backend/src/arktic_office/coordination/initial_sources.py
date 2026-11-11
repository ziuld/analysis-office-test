"""Seed specialist research from the existing snapshot, without model calls."""
import json
import re
import tomllib
from pathlib import PurePosixPath

from arktic_office.config.agents import FULL_STACK
from arktic_office.resources.paths import resource_path


def fragment(file, limit, anchor):
    lines = file['text'].splitlines()
    start = next((i for i, line in enumerate(lines) if anchor.search(line)), 0) if anchor else 0
    size = start
    selected = []
    for line in lines[start:]:
        size += len(line.encode()) + 1
        if size > limit:
            break
        selected.append(line)
    if not any(line.strip() for line in selected):
        return None
    return {'path': file['path'], 'text': '\n'.join([''] * start + selected),
            'partial': start > 0 or len(selected) != len(lines), 'start': start + 1, 'end': start + len(selected)}


def select(role, evidence, limits, *, with_groups=False):
    folder = resource_path('profiles', 'agents', role)
    if role == FULL_STACK:
        policy = tomllib.loads((folder / 'initial-sources.toml').read_text(encoding='utf-8'))
    else:
        config = folder / 'initial-sources.json'
        if not config.is_file():
            return [], None
        policy = json.loads(config.read_text(encoding='utf-8'))
    paths = sorted((PurePosixPath(path) for path in evidence.files), key=lambda path: (len(path.parts), str(path)))
    files, provided, matches, missing, seen = [], [], {}, [], set()
    remaining = min(policy['max_bytes'], limits['bytes'])
    file_limit = min(policy['max_files'], limits['files'])
    for group in policy['groups']:
        matched = list(dict.fromkeys(str(path) for pattern in group['patterns'] for path in paths
                                     if path.full_match(pattern, case_sensitive=False)))
        if not matched:
            missing.append(group['id'])
        anchor = re.compile(group['anchor']) if group.get('anchor') else None
        supplied = 0
        for path in matched:
            matches[path] = None
            if path in seen or supplied >= group['take'] or len(files) >= file_limit or remaining <= 0:
                continue
            item = fragment(evidence.files[path], min(remaining, policy['max_file_bytes']), anchor)
            if item:
                files.append(item)
                entry = {k: item[k] for k in ('path', 'start', 'end', 'partial')}
                if with_groups:
                    entry['group'] = group['id']
                provided.append(entry)
                seen.add(path)
                supplied += 1
                remaining -= len(item['text'].encode())
    pending = [path for path in matches if path not in seen]
    return files, {'provided': provided,
                   'pending_paths': pending[:12], 'pending_count': len(pending), 'unmatched_groups': missing,
                   'bytes': sum(len(f['text'].encode()) for f in files)}
