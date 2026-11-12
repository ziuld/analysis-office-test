"""Operator acknowledgement before code can reach a model."""
import os

from arktic_office.core.errors import AuditError


QUESTION = "¿Estás usando un entorno de IA privado autorizado para el código de este proyecto?"
REQUIRED = "Confirma el uso de un entorno de IA privado autorizado antes de ejecutar la revisión."


def confirmed(declared=False):
    return declared is True or os.environ.get("AUDIT_PRIVATE_AI_CONFIRMED") == "1"


def require_private_ai(declared=False):
    if not confirmed(declared):
        raise AuditError(REQUIRED)
