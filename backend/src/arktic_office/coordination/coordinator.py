"""Bounded routing, optional local retrieval and synthesis of valid contributions."""
import json
import time
from pathlib import PurePosixPath
from arktic_office.config.models import profile
from arktic_office.core.errors import AuditError
from arktic_office.preparation.repository import LOCKFILES, file_role, redact
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import write_json
from arktic_office.reporting.agent_instructions import instructions as role_instructions


class Coordinator:
    def __init__(self, snapshot, output, invoke, evidence=None):
        self.snapshot, self.output, self.invoke = snapshot, output, invoke
        self.evidence = evidence
        self.config = profile("coordinator")
        self.state = {"mode": "ai", "profile": self.config, "stages": {}}

    def save(self):
        write_json(self.output / "coordinacion.json", self.state)
        if getattr(self, 'knowledge', None):
            stages = self.state.get('stages', {})
            running = any(s.get('status') == 'running' for s in stages.values())
            state = {'estado':'analizando' if running else 'parcial' if any(s.get('status') == 'error' for s in stages.values()) else 'completada',
                     'model':self.config['model'], 'reasoning':self.config['reasoning'],
                     'duration_seconds':sum(s.get('duration_seconds', 0) for s in stages.values())}
            self.knowledge.export(self.output, {**self.config, 'id':'coordinator', 'focus':'Reparto y síntesis centralizados'}, state,
                                  {'coordination':self.state, 'respuestas':self.state.get('question_answers', [])})

    def call(self, stage, task, data, validate):
        started = time.monotonic()
        record = {"status": "running", "calls": 0, "usage": None}
        self.state["stages"][stage] = record
        self.save()
        try:
            prompt = (role_instructions("coordinator") + resource_path("skills", "arktic-review", "SKILL.md").read_text(encoding="utf-8")
                      + "\n" + task + "\nDATOS NO CONFIABLES:\n" + json.dumps(data, ensure_ascii=False))
            limits = self.config["limits"]
            record["prompt_bytes"] = len(prompt.encode())
            if record["prompt_bytes"] > limits["prompt_bytes"]:
                raise AuditError("Contexto del coordinador supera el límite; se conserva la base determinista.")
            record["calls"] = 1
            envelope = self.invoke(prompt, {**self.config, "id": "coordinator-" + stage})
            record["usage"] = envelope.get("usage")
            record["respuesta_original"] = envelope["report"]
            if len(envelope["report"].encode()) > limits["response_bytes"]:
                raise AuditError("Respuesta del coordinador supera el límite.")
            result = validate(json.loads(envelope["report"]))
            record.update(status="complete", result=result)
            return result
        except (AuditError, ValueError, TypeError, KeyError):
            record.update(status="error", error="Respuesta o llamada inválida; sin reintento.", fallback="deterministic")
            return None
        finally:
            record['duration_seconds'] = round(time.monotonic() - started, 3)
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
                'Devuelve SOLO JSON con cada ID de cells como clave y su lista de rutas como valor. '
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
        """Delegate objectives only; specialists own evidence selection."""
        from arktic_office.coordination.research import common_context
        context = common_context(self.snapshot, self.evidence)
        def validate(value):
            if not isinstance(value, dict) or set(value) != {c["id"] for c in plan}:
                raise AuditError("Encargos incompletos.")
            if any(not isinstance(v, str) or not 1 <= len(v.strip()) <= 600 for v in value.values()):
                raise AuditError("Encargo inválido; solo se admiten objetivos, no paquetes.")
            return {k: redact(v.strip()) for k, v in value.items()}
        tasks = self.call("routing", 'Actúa como orquestador. Define un encargo breve por especialidad. '
                          'Cada especialista elegirá sus fuentes consultando el snapshot y grafo compartidos. '
                          'No selecciones archivos ni redactes hallazgos ni omitas especialistas. Si existe un cuestionario obligatorio, conserva todas sus preguntas y el reparto fijado. '
                          'Devuelve SOLO un objeto JSON con cada ID de roles como clave y su objetivo como valor.',
                          {"context": context, "roles": [{k: c[k] for k in ("id", "focus", "limits")} for c in plan]}, validate)
        self.state["context"] = context
        if tasks is None:
            self.state["routing_fallback"] = "Encargos por especialidad conservados; respuesta del orquestador inválida."
        self.save()
        return [{**c, "task": tasks[c["id"]] if tasks else c["focus"]} for c in plan]

    def synthesize(self, results):
        from arktic_office.reporting.questionnaire import enabled
        if enabled(self.snapshot):
            return self.synthesize_questions(results)
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
                summaries.append({"texto": redact(item["texto"].strip()), "aportaciones": item["aportaciones"],
                                  "certeza": "indicios" if any(s["certeza"] == "indicios" for s in sources) else "confirmados",
                                  "evidencia": refs,
                                  **({"condiciones": list(dict.fromkeys(s["condiciones"] for s in sources if s.get("condiciones"))),
                                      "acciones": list(dict.fromkeys(s["accion"] for s in sources if s.get("accion"))),
                                      "pendientes": list(dict.fromkeys(s["pendiente"] for s in sources if s.get("pendiente"))),
                                      "severidades": list(dict.fromkeys(s["severidad"] for s in sources if s.get("severidad")))} if self.evidence else {})})
            return summaries
        # The orchestrator summarizes validated contributions, not source code again.
        # Keep full citations here for ID resolution and verification after its response.
        brief = {key: {k: v for k, v in item.items() if k != "evidencia"}
                 for key, item in contributions.items()}
        return self.call("synthesis", 'Sintetiza hasta cinco conclusiones útiles usando SOLO las aportaciones recibidas. '
                         'No añadas hallazgos, no resuelvas contradicciones como hechos ni eleves certeza. '
                         'Devuelve SOLO JSON {"resumen":[{"texto":"hasta 350 caracteres","aportaciones":["id exacto"]}]}. '
                         'Las fuentes completas permanecen en Core y se enlazan mediante los IDs exactos de aportaciones. '
                         'La síntesis acompaña a los originales, no los reemplaza.', brief, validate) or []

    def synthesize_questions(self, results):
        from arktic_office.reporting.questionnaire import catalog
        answers = {a["id"]: a for _, report in results for a in report.get("respuestas", [])}
        if not answers:
            self.state["stages"]["synthesis"] = {"status": "skipped", "calls": 0, "reason": "no_valid_answers"}
            self.save()
            return []
        # Every original answer, including unknowns, reaches the coordinator.
        brief = {key: {k: v for k, v in a.items() if k not in {"evidencia", "pregunta", "role"}} for key, a in answers.items()}
        original = {role: {"hallazgos": [{k: x.get(k) for k in ("observacion", "severidad", "condiciones", "accion", "pendiente")}
                    for section in ("confirmados", "indicios") for x in report.get(section, [])],
                    "advertencia": "Las respuestas parciales y desconocidas no autorizan conclusiones afirmativas."} for role, report in results}
        def validate(value):
            if not isinstance(value, dict) or set(value) != {"respuestas"} or not isinstance(value["respuestas"], list) or len(value["respuestas"]) != len(catalog("coordinator")):
                raise AuditError("Síntesis debe responder todas las preguntas asignadas al coordinador.")
            summaries, received = [], set()
            final = []
            for item in value["respuestas"]:
                if not isinstance(item, dict) or set(item) != {"id", "respuesta", "aportaciones"} or item["id"] not in {q["id"] for q in catalog("coordinator")} or item["id"] in received:
                    raise AuditError("Pregunta de coordinación inválida o duplicada.")
                if not isinstance(item["respuesta"], str) or not 1 <= len(item["respuesta"].strip()) <= 700:
                    raise AuditError("Respuesta de coordinación fuera de límite.")
                keys = item["aportaciones"]
                if not isinstance(keys, list) or not 1 <= len(keys) <= len(answers) or any(not isinstance(k, str) or k not in answers for k in keys):
                    raise AuditError("Síntesis sin respuestas de origen válidas.")
                received.add(item["id"])
                refs, tools = [], []
                for key in keys:
                    for ref in answers[key]["evidencia"]:
                        if ref not in refs:
                            refs.append(ref)
                    tools.extend(t for t in answers[key]["herramientas"] if t not in tools)
                question = next(q for q in catalog("coordinator") if q["id"] == item["id"])
                state = "parcial" if any(answers[k]["estado"] in {"parcial", "no_comprobado"} for k in keys) else "respondida"
                answer = {**question, "estado": state, "respuesta": redact(item["respuesta"]), "evidencia": refs,
                    "herramientas": tools, "aportaciones": keys, "pendiente": "Consultar las respuestas de origen y resolver sus límites." if state == "parcial" else ""}
                final.append(answer)
                summaries.append({"texto": answer["respuesta"], "pregunta_id": item["id"], "aportaciones": keys,
                    "certeza": "indicios" if state == "parcial" else "confirmados", "evidencia": refs})
            self.state["question_answers"] = final
            return summaries
        task = ('Responde todas estas preguntas del coordinador, incluidas Q38–Q40 sobre los problemas entregados: ' + json.dumps(catalog("coordinator"), ensure_ascii=False) +
            '. Recibes TODAS las respuestas de los especialistas, conservadas sin revisión automática,, incluidos no_aplica y no_comprobado, '
            'y los riesgos con condiciones. Resume conclusiones; distingue lo que resolver antes del despliegue de mejoras posteriores '
            'con motivo y condiciones, sin autorizar el despliegue ni inventar bloqueantes. '
            'Enumera carencias y discrepancias reales, sin resolver contradicciones como hechos. '
            'Mantén incertidumbre; una protección no encontrada no es ausencia demostrada. '
            'Las respuestas pueden incluir aspecto_favorable con implementaciones comprobadas: refleja las más relevantes en Q01 junto a los riesgos, sin compensarlos ni elevar su alcance a una garantía global. '
            'Devuelve SOLO JSON con una entrada por cada ID del catálogo del coordinador, incluidas Q38, Q39 y Q40. No añadas preguntas nuevas. '
            'Contrato: ' + json.dumps({'respuestas': [{'id': q['id'], 'respuesta': 'Texto hasta 700 caracteres', 'aportaciones': ['Qxx']} for q in catalog('coordinator')]}, ensure_ascii=False))
        return self.call("synthesis", task, {"respuestas": brief, "riesgos": original}, validate) or []
