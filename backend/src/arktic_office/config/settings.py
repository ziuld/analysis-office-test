"""Compatibility entry points backed by the local model registry."""
from arktic_office.config.models import settings, runtime_options, profile


def cell_config(cell):
    return profile(cell["id"])


def reports_root():
    import os
    from pathlib import Path
    return Path(os.environ.get("AUDIT_REPORTS_DIR", "/reports"))
