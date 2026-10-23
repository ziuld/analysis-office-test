"""Package-owned resources plus the one canonical shared editorial document."""
from importlib.resources import files
from pathlib import Path
import sys

from arktic_office.core.errors import AuditError


def resource_path(*parts):
    return Path(str(files("arktic_office.resources").joinpath(*parts)))


def standard_path():
    relative = Path("docs/ESTANDAR_COMUNICACION_INFORMES.md")
    # Installed wheel: data-files installs under the interpreter's prefix.
    installed = Path(sys.prefix) / "share/arktic-office" / relative
    if installed.is_file():
        return installed
    # src/editable checkout: keep reading the canonical document, not a copy.
    checkout = Path(__file__).resolve().parents[4] / relative
    if checkout.is_file():
        return checkout
    raise AuditError("Falta el estándar editorial compartido; revisar la instalación.")
