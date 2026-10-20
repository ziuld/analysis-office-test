import os

from repository import AuditError


def settings():
    provider = os.environ.get("AUDIT_PROVIDER", "openai-codex").strip()
    if provider not in {"openai", "openai-codex"}:
        raise AuditError("AUDIT_PROVIDER debe ser openai-codex (suscripción) u openai (API).")
    default = "gpt-6-luna" if provider == "openai-codex" else "gpt-5.4-mini"
    return provider, os.environ.get("AUDIT_MODEL", "").strip() or default


def runtime_options():
    effort = os.environ.get("AUDIT_REASONING", "low").strip()
    if effort not in {"low", "medium", "high"}:
        raise AuditError("AUDIT_REASONING debe ser low, medium o high.")
    try:
        output = int(os.environ.get("AUDIT_MAX_OUTPUT_TOKENS", "2500"))
    except ValueError:
        raise AuditError("AUDIT_MAX_OUTPUT_TOKENS debe ser un número entero.") from None
    if not 1000 <= output <= 8000:
        raise AuditError("AUDIT_MAX_OUTPUT_TOKENS debe estar entre 1000 y 8000.")
    return {"max_tokens": output, "reasoning_config": {"effort": effort}}
