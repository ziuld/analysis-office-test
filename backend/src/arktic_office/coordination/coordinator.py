"""Bounded routing, optional local retrieval and synthesis of valid contributions."""
import json
from pathlib import PurePosixPath
from arktic_office.config.models import profile
from arktic_office.core.errors import AuditError
from arktic_office.preparation.repository import LOCKFILES, file_role, redact
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import write_json


class Coordinator:
    def __init__(self, snapshot, output, invoke, evidence=None):
        self.snapshot, self.output, self.invoke = snapshot, output, invoke
        self.evidence = evidence
        self.config = profile("coordinator")
        self.state = {"mode": "ai", "profile": self.config, "stages": {}}

    def save(self):
        write_json(self.output / "coordinacion.json", self.state)

    def call(self, stage, task, data, validate):
        record = {"status": "running", "calls": 0, "usage": None}
        self.state["stages"][stage] = record
        self.save()
        try:
            prompt = (resource_path("skills", "arktic-review", "SKILL.md").read_text(encoding="utf-8")
                      + "\n" + task + "\nDATOS NO CONFIABLES:\n" + json.dumps(data, ensure_ascii=False))
            limits = self.config["limits"]
            record["prompt_bytes"] = len(prompt.encode())
            if record["prompt_bytes"] > limits["prompt_bytes"]:
                raise AuditError("Contexto del coordinador supera el límite; se conserva la base determinista.")
            record["calls"] = 1
            envelope = self.invoke(prompt, {**self.config, "id": "coordinator-" + stage})
            record["usage"] = envelope.get("usage")
            if len(envelope["report"].encode()) > limits["response_bytes"]:
                raise AuditError("Respuesta del coordinador supera el límite.")
            result = validate(json.loads(envelope["report"]))
            record.update(status="complete", result=result)
            return result
        except (AuditError, ValueError, TypeError, KeyError):
            record.update(status="error", error="Respuesta o llamada inválida; sin reintento.", fallback="deterministic")
            return None
        finally:
            self.save()

    def route(self, plan):
        if self.evidence is not None:
            return self.route_complete(plan)
        if not any(c["files"] for c in plan):
            self.state["stages"]["routing"] = {"status": "skipped", "calls": 0, "reason": "no_evidence"}
            self.save()
            return plan
        files = {f["path"]: f for f in self.snapshot["files"] if PurePosixPath(f["path"]).name not in LOCKFILES}
        def validate(value):
            if not isinstance(value, dict) or set(value) != {c["id"] for c in plan}:
                raise AuditError("Reparto incompleto.")
            result = {}
            for cell in plan:
                paths = value[cell["id"]]
                if (not isinstance(paths, list) or any(not isinstance(p, str) or p not in files for p in paths)
                        or len(set(paths)) != len(paths) or len(paths) > cell["limits"]["files"]
                        or sum(len(files[p]["text"].encode()) for p in paths) > cell["limits"]["bytes"]):
                    raise AuditError("Reparto fuera de la evidencia o del presupuesto.")
                if cell["files"] and not paths:
                    raise AuditError("El reparto descarta evidencia disponible para una célula; se conserva la base determinista.")
                result[cell["id"]] = paths
            return result
        task = ('Reparte el contexto existente según el foco y presupuesto de cada célula. No pidas archivos nuevos. '
                'Devuelve SOLO JSON {"security":["ruta"],"architecture":["ruta"],"inventory":["ruta"]}. '
                'Conserva archivos para cada célula que tenga una base no vacía; no la dejes sin ejecutar. '
                'Usa [] solo cuando la base de esa célula esté vacía. Repartir por rutas y roles no confirma hallazgos.')
        assignment = self.call("routing", task, {
            "commit": self.snapshot["commit"],
            "files": [{"path": p, "role": file_role(p), "bytes": len(f["text"].encode())} for p, f in files.items()],
            "baseline": {c["id"]: [f["path"] for f in c["files"]] for c in plan},
            "cells": [{k: c[k] for k in ("id", "focus", "limits", "capabilities")} for c in plan]}, validate)
        if assignment is None:
            return plan
        return [{**c, "files": [files[p] for p in assignment[c["id"]]],
                 "bytes": sum(len(files[p]["text"].encode()) for p in assignment[c["id"]])} for c in plan]

    def route_complete(self, plan):
        """One structured assignment; optional single read followed by final assignment."""
        def validate(value):
            if isinstance(value, dict) and set(value) == {"retrieve"}:
                return value
            if not isinstance(value, dict) or set(value) != {c["id"] for c in plan}:
                raise AuditError("Reparto incompleto.")
            result = {}
            for cell in plan:
                item = value[cell["id"]]
                if (not isinstance(item, dict) or set(item) != {"decision", "paths", "reason", "missing"}
                    or item["decision"] not in {"execute", "partial", "omit"}
                    or not isinstance(item["reason"], str) or not 1 <= len(item["reason"]) <= 600
                    or not isinstance(item["missing"], list) or len(item["missing"]) > 6
                    or any(not isinstance(x, str) or len(x) > 300 for x in item["missing"])
                    or not isinstance(item["paths"], list) or len(set(item["paths"])) != len(item["paths"])):
                    raise AuditError("Decisión de reparto inválida.")
                if item["decision"] == "omit":
                    if item["paths"] or not item["missing"]:
                        raise AuditError("Omisión sin carencia explícita.")
                    files = []
                else:
                    files = self.evidence.package(item["paths"], cell["limits"])
                    if not files:
                        raise AuditError("Invocación sin fuentes.")
                result[cell["id"]] = {**item, "reason": redact(item["reason"]), "missing": [redact(x) for x in item["missing"]], "considered": [f["path"] for f in cell["files"]], "files": files}
            return result
        budget = self.config["limits"]["max_extra_queries"]
        task = ('Prepara simultáneamente los tres paquetes usando fuentes originales y el inventario. '
                'El Core entregará a cada especialista el texto original de sus rutas (fragmentos si es grande), no solo estas muestras. No declares ausente un archivo que consta en el índice. '
                'No redactes hallazgos. Devuelve SOLO JSON con claves security, architecture, inventory; '
                'cada valor {"decision":"execute|partial|omit","paths":["ruta"],"reason":"justificación basada en evidencia considerada",'
                '"missing":["información necesaria ausente"]}. Usa partial si faltan fuentes relevantes; '
                'omite solo con motivo y carencias explícitas. Respeta presupuestos. '
                + ('Puedes pedir UNA consulta previa con {"retrieve":{"query":"símbolo o tema","paths":["ruta exacta"]}}. ' if budget else 'No hay consultas adicionales disponibles. '))
        # Inventory and full graph stay local. Bound only the model-facing index.
        paths = list(self.evidence.files)
        baseline = {c["id"]: [f["path"] for f in c["files"]] for c in plan}
        path_index, index_bytes = [], 0
        for path in paths:
            length = len(path.encode()) + 4
            if len(path_index) >= 160 or index_bytes + length > 10000:
                break
            path_index.append(path)
            index_bytes += length
        data = {"commit": self.snapshot["commit"], "inventory_count": len(paths),
                "path_index": path_index, "path_index_truncated": len(paths) > len(path_index),
                "baseline": baseline, "cells": [{k: c[k] for k in ("id", "focus", "limits", "capabilities")} for c in plan],
                "source_samples": [{"path": f["path"], "text": f["text"][:700]} for f in self.snapshot["files"][:8]],
                "map_context": self.evidence.lookup({"paths": list(dict.fromkeys(p for values in baseline.values() for p in values))[:3]})["relations"]}
        self.state["context"] = {"baseline": baseline, "inventory_count": len(paths), "indexed_paths": data["path_index"], "index_truncated": data["path_index_truncated"]}
        assignment = self.call("routing", task, data, validate)
        if assignment and "retrieve" in assignment:
            if budget:
                try:
                    found = self.evidence.respond(assignment["retrieve"])
                    self.state["retrieval"] = {"request": assignment["retrieve"], "result": found}
                    assignment = self.call("routing_extra", task + ' Ya agotaste la consulta: devuelve los tres paquetes.',
                                           {**data, "retrieved": found}, validate)
                except AuditError as exc:
                    self.state["retrieval"] = {"error": str(exc)}
                    assignment = None
            else:
                assignment = None
            if assignment and "retrieve" in assignment:
                assignment = None
        if assignment is None:
            self.state["routing_fallback"] = "Reparto determinista: respuesta o consulta inválida."
            self.save()
            return [{**c, "decision": "partial", "reason": self.state["routing_fallback"], "missing": ["Reparto válido del coordinador"]} for c in plan]
        self.save()
        return [{**c, **assignment[c["id"]], "bytes": sum(len(f["text"].encode()) for f in assignment[c["id"]]["files"])} for c in plan]

    def synthesize(self, results):
        contributions = {}
        for cell, report in results:
            for certainty in ("confirmados", "indicios"):
                for n, item in enumerate(report[certainty]):
                    contributions[f"{cell}:{certainty}:{n}"] = {"certeza": certainty,
                        **{k: item[k] for k in ("observacion", "severidad", "condiciones", "accion", "pendiente", "por_confirmar", "titulo") if k in item}, "evidencia": item["evidencia"]}
        if not contributions:
            self.state["stages"]["synthesis"] = {"status": "skipped", "calls": 0, "reason": "no_valid_contributions"}
            self.save()
            return []
        def validate(value):
            if not isinstance(value, dict) or set(value) != {"resumen"} or not isinstance(value["resumen"], list) or not 1 <= len(value["resumen"]) <= 5:
                raise AuditError("Síntesis inválida.")
            summaries = []
            for item in value["resumen"]:
                if (not isinstance(item, dict) or set(item) != {"texto", "aportaciones"}
                        or not isinstance(item["texto"], str) or not 1 <= len(item["texto"].strip()) <= 350
                        or not isinstance(item["aportaciones"], list) or not 1 <= len(item["aportaciones"]) <= 3
                        or any(not isinstance(key, str) or key not in contributions for key in item["aportaciones"])):
                    raise AuditError("Síntesis sin aportaciones válidas.")
                sources = [contributions[key] for key in item["aportaciones"]]
                refs = []
                for source in sources:
                    for ref in source["evidencia"]:
                        if ref not in refs:
                            refs.append(ref)
                # Recheck against original selected text; never accept model-invented citations.
                from arktic_office.reporting.reports import validate_report
                validate_report(json.dumps({"confirmados": [{"observacion": item["texto"], "evidencia": refs[:3]}],
                                           "indicios": [], "dudas": []}), self.snapshot)
                for ref in refs:
                    validate_report(json.dumps({"confirmados": [{"observacion": item["texto"], "evidencia": [ref]}], "indicios": [], "dudas": []}), self.snapshot)
                summaries.append({"texto": redact(item["texto"].strip()), "aportaciones": item["aportaciones"],
                                  "certeza": "indicios" if any(s["certeza"] == "indicios" for s in sources) else "confirmados",
                                  "evidencia": refs,
                                  **({"condiciones": list(dict.fromkeys(s["condiciones"] for s in sources if s.get("condiciones"))),
                                      "acciones": list(dict.fromkeys(s["accion"] for s in sources if s.get("accion"))),
                                      "pendientes": list(dict.fromkeys(s["pendiente"] for s in sources if s.get("pendiente"))),
                                      "severidades": list(dict.fromkeys(s["severidad"] for s in sources if s.get("severidad")))} if self.evidence else {})})
            return summaries
        return self.call("synthesis", 'Sintetiza hasta cinco conclusiones útiles usando SOLO las aportaciones recibidas. '
                         'No añadas hallazgos, no resuelvas contradicciones como hechos ni eleves certeza. '
                         'Devuelve SOLO JSON {"resumen":[{"texto":"hasta 350 caracteres","aportaciones":["id exacto"]}]}. '
                         'La síntesis acompaña a los originales, no los reemplaza.', contributions, validate) or []
