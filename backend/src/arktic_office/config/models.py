"""Local profiles; validation never probes providers or spends model quota."""
import json
import os
import re
from functools import lru_cache
from arktic_office.core.errors import AuditError
from arktic_office.resources.paths import resource_path


@lru_cache(maxsize=1)
def registry():
    return json.loads(resource_path("profiles", "models.json").read_text(encoding="utf-8"))


def settings():
    provider = os.environ.get("AUDIT_PROVIDER", "openai-codex").strip()
    if provider not in registry()["providers"]:
        raise AuditError("AUDIT_PROVIDER debe ser openai-codex (suscripción) u openai (API).")
    model = os.environ.get("AUDIT_MODEL", "").strip() or registry()["providers"][provider]
    validate_model(model)
    return provider, model


def validate_model(model):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model):
        raise AuditError("Identificador de modelo inválido; revisar la configuración local.")


def integer(name, default, low, high):
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise AuditError(name + " debe ser un número entero.") from None
    if not low <= value <= high:
        raise AuditError(f"{name} debe estar entre {low} y {high}.")
    return value


def runtime_options():
    effort = os.environ.get("AUDIT_REASONING", "low").strip()
    if effort not in registry()["reasoning"]:
        raise AuditError("AUDIT_REASONING debe ser low, medium o high.")
    output = integer("AUDIT_MAX_OUTPUT_TOKENS", 4500, 1000, 8000)
    return {"max_tokens": output, "reasoning_config": {"effort": effort}}


def profile(role):
    provider, model = settings()
    options = runtime_options()
    limits = dict(registry()["roles"][role])
    prefix = "AUDIT_" + role.upper()
    if role != "preparation":
        limits["max_extra_queries"] = integer(prefix + "_MAX_EXTRA_QUERIES", 0, 0, 1)
        limits["calls"] = (2 if role == "coordinator" else 1) + limits["max_extra_queries"]
    if role in {"security", "architecture", "inventory"}:
        limits["research_rounds"] = integer(prefix + "_RESEARCH_ROUNDS", 1, 0, 2)
        limits["calls"] = 1 + limits["research_rounds"]
    if role == "preparation":
        limits["max_loops"] = integer(prefix + "_MAX_LOOPS", limits["max_loops"], 0, 20)
        limits["iterations"] = 1 + limits["max_loops"]
    model = os.environ.get(prefix + "_MODEL", "").strip() or model
    validate_model(model)
    effort = os.environ.get(prefix + "_REASONING", "").strip() or options["reasoning_config"]["effort"]
    if effort not in registry()["reasoning"]:
        raise AuditError(prefix + "_REASONING debe ser low, medium o high.")
    return {"provider": provider, "model": model, "reasoning": effort,
            "max_output_tokens": integer(prefix + "_MAX_OUTPUT_TOKENS",
                                         min(options["max_tokens"], limits["output_tokens"]), 1000, 8000),
            "timeout": limits["seconds"], "limits": limits}


def request_options():
    mode = os.environ.get("AUDIT_COORDINATION_MODE", "deterministic").strip()
    if mode not in {"deterministic", "ai"}:
        raise AuditError("AUDIT_COORDINATION_MODE debe ser deterministic o ai.")
    capabilities = [v.strip() for v in os.environ.get("AUDIT_CAPABILITIES", "").split(",") if v.strip()]
    if set(capabilities) - {"azure"}:
        raise AuditError("Capacidad no admitida en AUDIT_CAPABILITIES; se admite azure.")
    return {"mode": mode, "capabilities": sorted(set(capabilities))}


def validate_configuration():
    """Validate every role before preparation or the first coordination call."""
    request_options()
    scanners_enabled()
    return {role: profile(role) for role in registry()["roles"]}


def scanners_enabled():
    return bool(integer("AUDIT_SCANNERS_ENABLED", 1, 0, 1))
