"""Hermes process adapter; no model calls at import time."""
import json
import os
import subprocess
import sys
from arktic_office.core.errors import AuditError, SpecialistTimeout


class ProviderError(AuditError):
    global_stop = True


def normalize_json_report(raw):
    """Remove only a known transport suffix after an otherwise complete JSON object."""
    value = raw.rstrip()
    if value.endswith("</final>"):
        candidate = value[:-8].rstrip()
        try:
            if isinstance(json.loads(candidate), dict):
                return candidate
        except ValueError:
            pass
    return raw


def invoke_hermes(prompt, config):
    env = dict(os.environ, AUDIT_MODEL=config["model"], AUDIT_REASONING=config["reasoning"])
    if "provider" in config:
        env["AUDIT_PROVIDER"] = config["provider"]
    if env.get("AUDIT_PROVIDER", "openai-codex").strip() == "openai-codex":
        env.setdefault("HERMES_CODEX_EVENT_STALE_TIMEOUT_SECONDS", "90")
    if "max_output_tokens" in config:
        env["AUDIT_MAX_OUTPUT_TOKENS"] = str(config["max_output_tokens"])
    timeout = max(1, min(float(config.get("timeout", 240)), 240))
    try:
        result = subprocess.run([sys.executable, "-m", "arktic_office.adapters.hermes_runtime"], input=prompt, text=True,
                                capture_output=True, timeout=timeout, check=False, env=env)
    except subprocess.TimeoutExpired:
        if config.get("timeout_scope") == "specialist":
            raise SpecialistTimeout("Se agotó el plazo local del especialista. Resultado y consumo remotos desconocidos; se conserva el avance.") from None
        raise ProviderError("Hermes superó el tiempo permitido; resultado remoto desconocido; no se reintentó.") from None
    if result.returncode:
        reasons = {"quota_or_rate_limit": "cuota o límite de peticiones", "unsupported_model": "modelo no admitido por el proveedor", "authentication": "sesión no válida", "timeout": "tiempo agotado", "incomplete_response": "respuesta incompleta"}
        try:
            code = json.loads(result.stderr).get("code")
        except (ValueError, AttributeError):
            code = None
        raise ProviderError("Hermes no completó la célula: " + reasons.get(code, "fallo de sesión, modelo o conexión") + ". Sin reintento automático.")
    try:
        envelope = json.loads(result.stdout)
        if not isinstance(envelope, dict) or not isinstance(envelope.get("report"), str):
            raise ValueError()
    except (ValueError, TypeError):
        raise AuditError("El runtime no devolvió una respuesta estructurada válida.") from None
    normalized = normalize_json_report(envelope["report"])
    if normalized != envelope["report"]:
        envelope["report"] = normalized
        envelope["format_normalization"] = "removed_final_closing_tag"
    return envelope

