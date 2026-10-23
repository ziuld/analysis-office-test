"""Hermes process adapter; no model calls at import time."""
import json
import os
import subprocess
import sys
from arktic_office.core.errors import AuditError


def invoke_hermes(prompt, config):
    env = dict(os.environ, AUDIT_MODEL=config["model"], AUDIT_REASONING=config["reasoning"])
    try:
        result = subprocess.run([sys.executable, "-m", "arktic_office.adapters.hermes_runtime"], input=prompt, text=True,
                                capture_output=True, timeout=240, check=False, env=env)
    except subprocess.TimeoutExpired:
        raise AuditError("La célula superó 240 segundos; no se reintentó.") from None
    if result.returncode:
        reasons = {"quota_or_rate_limit": "cuota o límite de peticiones", "unsupported_model": "modelo no admitido por el proveedor", "authentication": "sesión no válida", "timeout": "tiempo agotado", "incomplete_response": "respuesta incompleta"}
        try:
            code = json.loads(result.stderr).get("code")
        except (ValueError, AttributeError):
            code = None
        raise AuditError("Hermes no completó la célula: " + reasons.get(code, "fallo de sesión, modelo o conexión") + ". Sin reintento automático.")
    try:
        envelope = json.loads(result.stdout)
        if not isinstance(envelope, dict) or not isinstance(envelope.get("report"), str):
            raise ValueError()
    except (ValueError, TypeError):
        raise AuditError("El runtime no devolvió una respuesta estructurada válida.") from None
    return envelope

