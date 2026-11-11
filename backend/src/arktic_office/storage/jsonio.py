"""JSON serialization compatible with existing BOM files and atomic writes."""
import json
import time


def read_json(path, fallback=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return fallback


def write_json(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    # A reader on a Windows bind mount can briefly prevent atomic replacement.
    for delay in (0.05, 0.1, 0.2, 0.4):
        try:
            temp.replace(path)
            return
        except PermissionError:
            time.sleep(delay)
    temp.replace(path)
