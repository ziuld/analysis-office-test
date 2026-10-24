"""Package-owned resources plus the one canonical shared editorial document."""
from importlib.resources import files
from pathlib import Path


def resource_path(*parts):
    return Path(str(files("arktic_office.resources").joinpath(*parts)))


def standard_path():
    return resource_path("editorial", "standard.md")
