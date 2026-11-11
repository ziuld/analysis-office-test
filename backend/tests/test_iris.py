"""Offline review of the task contract, checkpoints and report assembly."""
import json
import os
import re
import shutil
import tempfile
import tomllib
import unittest
from collections import Counter
from html import escape
from pathlib import Path
from unittest.mock import patch

from arktic_office.adapters.invoke import ProviderError
from arktic_office.config.agents import FULL_STACK
from arktic_office.coordination.iris import checkpoint_path, interrupt, load_tasks
from arktic_office.coordination.team import run_team
from arktic_office.core.errors import AuditError
from arktic_office.preparation.evidence import Evidence
from arktic_office.reporting.questionnaire import catalog
from arktic_office.reporting.reading import GROUPS
from arktic_office.reporting.view import render_html, render_markdown
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import read_json
from test_questionnaire import fixture


PROFILE = resource_path("profiles", "agents", FULL_STACK)
CASES = tomllib.loads((PROFILE / "evals" / "casos.toml").read_text(encoding="utf-8"))


def iris_fixture():
    snapshot, evidence = fixture()
    snapshot["request"]["full_stack"] = True
    files = {"package.json": '{"name":"application"}', "db/schema.sql": "DATA_ONLY",
             "service/auth.py": "SECURITY_ONLY", "Dockerfile": "OPERATION_SEED",
             "src/client.py": "\n".join(["filler"] * 220 + ["def external_client():", "    return 'VERIFIED'", "TAIL_ONLY"])}
    evidence.files.update({path: {"path": path, "text": text} for path, text in files.items()})
    return snapshot, evidence


def response(**result):
    return {"report": json.dumps(result), "usage": {"input_tokens": 100, "output_tokens": 50}}


def answer(key, ref=None, **extra):
    return {"id": key, "estado": "respondida", "respuesta": "Resultado de Iris " + key,
            "evidencia": [ref] if ref else [], **extra}


def prompt_json(prompt, start, end):
    return json.loads(prompt.split(start, 1)[1].split(end, 1)[0])


class IrisTests(unittest.TestCase):
    def test_workflow_matches_the_existing_report_and_rejects_duplicate_coverage(self):
        tasks = load_tasks()
        report_groups = {}
        for task in tasks:
            group = "seguridad" if task["id"].startswith("seguridad-") else task["id"]
            report_groups.setdefault(group, []).extend(task["questions"])
        self.assertEqual({group: sorted(ids) for group, ids in report_groups.items()},
                         {group: [f"Q{n:02}" for n in numbers] for group, _, numbers in GROUPS})
        self.assertEqual(tasks[-1]["questions"], CASES["cobertura"]["sintesis"])
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder) / "iris"
            shutil.copytree(PROFILE, profile)
            guide = profile / tasks[0]["guide"]
            original = guide.read_text(encoding="utf-8")
            question = next(line for line in original.splitlines() if line.startswith("### Q04"))
            guide.write_text(original + "\n" + question + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "cada pregunta"):
                load_tasks(profile)
            guide.write_text(original.replace(question, "### Q04 · Texto distinto"), encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "no coinciden con el catálogo"):
                load_tasks(profile)

    def test_calls_isolate_questions_and_reuse_saved_citations(self):
        snapshot, evidence = iris_fixture()
        evidence.graph["nodes"].append({"id": "client", "label": "external_client", "source_file": "src/client.py",
                                        "source_location": "L221"})
        tasks = {task["id"]: task["questions"] for task in load_tasks()}
        calls = Counter()
        references = {}

        def invoke(prompt, config):
            self.assertEqual(config["id"], FULL_STACK)
            task = config["task_id"]
            calls[task] += 1
            block = prompt.split("\nTAREA ACTIVA\n", 1)[1].split("\nFIN DE TAREA ACTIVA.", 1)[0]
            self.assertEqual(re.findall(r"^### (Q\d{2}) · ", block, re.MULTILINE), tasks[task])
            self.assertIn("## Evidencia", block)
            self.assertIn("## Cierre", block)
            self.assertTrue(prompt.startswith((PROFILE / "AGENT.md").read_text(encoding="utf-8")))
            self.assertNotIn("En la oficina, activa", prompt)
            for question in catalog():
                self.assertEqual(question["pregunta"] in prompt, question["id"] in tasks[task])
            sources = {item["path"]: item for item in prompt_json(prompt, "FUENTES NO CONFIABLES: ", "\nFIN DE FUENTES.")}
            kwargs = {"comprobar": ["Contrastar el flujo descrito en las fuentes."]}
            if task == "aplicacion":
                self.assertIn("package.json", sources)
                self.assertNotIn("DATA_ONLY", prompt)
                self.assertNotIn("SECURITY_ONLY", prompt)
                if calls[task] == 1:
                    self.assertIn('hasta 4 consultas por ronda', prompt)
                    self.assertIn('como máximo 3 rutas en "paths" y 120 caracteres en "query"', prompt)
                    self.assertNotIn("src/client.py", sources)
                    return response(**kwargs, queries=[
                        {"query": "external_client", "paths": ["src/client.py"]},
                        {"paths": ["src/client.py"], "start_line": 222},
                    ])
                self.assertIn("L222 |     return 'VERIFIED'", sources["src/client.py"]["content"])
                references["client"] = sources["src/client.py"]["id"] + ":L222"
                references["symbol"] = sources["src/client.py"]["id"] + ":L221"
            if task == "estructura":
                if calls[task] == 1:
                    self.assertNotIn("src/client.py", sources)
                    return response(**kwargs, queries=[{"questions": ["Q06"]}, {"citations": [references["symbol"]]}])
                self.assertIn("Resultado de Iris Q06", prompt)
                self.assertEqual(sources["src/client.py"]["content"], "L221 | def external_client():\nL222 |     return 'VERIFIED'")
                self.assertNotIn("TAIL_ONLY", prompt)
            if task == "seguridad-identidad-frontend":
                if calls[task] == 1:
                    context = prompt_json(prompt, "CONTEXTO DE TAREA NO CONFIABLE: ", "\n")
                    indexed = next(f for f in context["previous"]["source_index"]["files"] if f["path"] == "src/client.py")
                    self.assertEqual(indexed["symbols"], [{"name": "external_client", "line": 221}])
                    self.assertTrue(indexed["ranges"])
                    self.assertNotIn("src/client.py", sources)
                    return response(**kwargs, queries=[{"citations": [references["client"]]}])
                self.assertEqual(sources["src/client.py"]["content"], "L222 |     return 'VERIFIED'")
            if task == "alcance":
                self.assertIn("Resultado de Iris Q06", prompt)
                self.assertIn("Resultado de Iris Q08", prompt)
                self.assertNotIn("SECURITY_ONLY", prompt)
                self.assertIn("L222 |     return 'VERIFIED'", sources["src/client.py"]["content"])
                self.assertIn("No hay rondas", prompt)
            ref = references.get("client") if task in {"aplicacion", "estructura", "alcance"} else None
            if task == "aplicacion":
                # Out-of-scope, duplicate and fabricated references cannot enter another block.
                items = [answer("Q06", ref, aspecto_favorable={"titulo": "Cliente separado", "detalle": "El cliente tiene su propia función."}),
                         answer("Q06", None, estado="no_comprobado"), answer("Q40", ref)]
                items.extend(answer(key, ref) for key in tasks[task] if key != "Q06")
            else:
                items = [answer(key, ref) for key in tasks[task]]
            if task == "datos":
                items[0].update(estado="parcial", pendiente="Falta la configuración de retención de la base.")
                items[1]["evidencia"] = [references["client"]]
                kwargs["pendientes"] = ["Confirmar la retención declarada para restauraciones."]
            return response(**kwargs, cierre="Bloque contrastado con la captura.", respuestas=items)

        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            report = run_team(snapshot, directory, invoke=invoke, evidence=evidence, emit=lambda *_args, **_kw: None)
            progress = read_json(checkpoint_path(directory))
        self.assertEqual(calls, {**dict.fromkeys(tasks, 1), "aplicacion": 2, "estructura": 2,
                                 "seguridad-identidad-frontend": 2})
        self.assertEqual(report["coordination"]["stages"]["synthesis"]["calls"], 1)
        answers = {item["id"]: item for item in report["cuestionario"]["respuestas"]}
        self.assertEqual(list(answers), [question["id"] for question in catalog()])
        self.assertEqual(len(report["cuestionario"]["respuestas"]), CASES["cobertura"]["preguntas"])
        self.assertTrue(all(item["role"] == FULL_STACK for item in answers.values()))
        citation_case = CASES["evidencia"]
        for key in citation_case["reutilizacion"]:
            self.assertEqual(answers[key]["evidencia"], answers[citation_case["origen"]]["evidencia"])
        self.assertEqual(answers[citation_case["fuera_del_bloque"]]["evidencia"], [])
        self.assertEqual(answers["Q10"]["pendiente"], "Falta la configuración de retención de la base.")
        self.assertEqual(progress["tasks"][2]["status"], "parcial")
        self.assertTrue(all(task["checks"] for task in progress["tasks"]))
        self.assertGreater(report["metrics"]["calls"][3]["context_sections"]["repeated_source_bytes"], 0)
        html, markdown = render_html(report, snapshot), render_markdown(report, snapshot)
        for artifact in (html, markdown):
            self.assertIn("Iris · Full Stack", artifact)
            self.assertIn("Confirmar la retención declarada para restauraciones.", artifact)
        for question in catalog():
            self.assertEqual(html.count(escape(question["pregunta"])), 1)
            self.assertEqual(markdown.count(question["pregunta"]), 1)

    def test_security_retains_two_rounds_and_publishes_a_cited_risk(self):
        snapshot, evidence = iris_fixture()
        target = {"path": "server/accounts.py", "text": "def get_account(account_id):\n    return accounts.get(account_id)"}
        evidence.files[target["path"]] = target
        calls = Counter()
        security = ("seguridad-identidad-frontend", "seguridad-backend-datos")

        def invoke(prompt, config):
            task = config["task_id"]
            calls[task] += 1
            step = calls[task]
            reply = {"comprobar": ["Seguir el acceso a una cuenta."], "cierre": "Falta comprobar el permiso del llamador."}
            if task in security and step == 1:
                self.assertIn("Quedan 2 rondas", prompt)
                return response(**reply, queries=[{"query": "get_account", "paths": ["server"]},
                                                  {"query": "get_account|accounts"}])
            if task in security and step == 2:
                self.assertIn("Quedan 1 rondas", prompt)
                self.assertIn("Ninguna ruta identifica un archivo", prompt)
                self.assertIn("La búsqueda es literal", prompt)
                self.assertNotIn("accounts.get(account_id)", prompt)
                return response(**reply, queries=[{"paths": [target["path"]]}])
            if task in security:
                self.assertIn("No hay rondas", prompt)
                files = prompt_json(prompt, "FUENTES NO CONFIABLES: ", "\nFIN DE FUENTES.")
                ref = next(file["id"] + ":L2" for file in files if file["path"] == target["path"])
                if task == security[0]:
                    reply["observaciones"] = [{"observacion": "La consulta de cuenta usa el ID recibido sin comprobar propietario.",
                        "certeza": "indicio", "tipo": "vulnerabilidad",
                        "condicion": "Debe comprobarse si el llamador verifica el propietario.", "evidencia": [ref]}]
                    reply["controles"] = [{"id": "acceso", "estado": "hallazgo", "motivo": "Falta verificar el llamador.", "evidencia": [ref]}]
                else:
                    reply["controles"] = [{"id": "entradas", "estado": "no_evaluado", "motivo": "Falta verificar la entrada.", "evidencia": []},
                                          {"id": "acceso", "estado": "no_evaluado", "motivo": "Fuera del bloque.", "evidencia": []}]
                return response(**reply)
            if re.search(r"Quedan \d+ rondas", prompt):
                return response(**reply, queries=[{"list_paths": True}])
            return response(**reply)

        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"AUDIT_FULL_STACK_CODE_ANALYST_RESEARCH_ROUNDS": "11"}):
            report = run_team(snapshot, Path(folder), invoke=invoke, evidence=evidence)
        self.assertEqual(calls.total(), 18)
        self.assertEqual([calls[task] for task in security], [3, 3])
        self.assertEqual(report["indicios"][0]["tipo"], "vulnerabilidad")
        self.assertEqual(report["indicios"][0]["evidencia"][0]["path"], target["path"])
        self.assertEqual(next(c["estado"] for c in report["controles"] if c["id"] == "acceso"), "hallazgo")
        self.assertEqual(report["indicios"][0]["severidad"], "informativa")
        html = render_html(report, snapshot)
        self.assertIn('<article id="R01"', html)
        self.assertIn("Gravedad sin determinar", html)
        self.assertIn("Gravedad sin determinar", render_markdown(report, snapshot))

    def test_budget_preserves_a_partial_turn_and_marks_remaining_work(self):
        snapshot, evidence = iris_fixture()
        case = CASES["cierre_parcial"]

        def invoke(prompt, config):
            self.assertEqual(config["task_id"], "aplicacion")
            return response(comprobar=["Rastrear el cliente externo."], respuestas=[
                answer(case["conservada"], estado="parcial", pendiente="Comprobar los scripts del repositorio.")],
                queries=[{"paths": ["src/client.py"]}])

        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"AUDIT_REVIEW_MAX_CALLS": str(case["max_llamadas"])}):
            directory = Path(folder)
            report = run_team(snapshot, directory, invoke=invoke, evidence=evidence)
            progress = read_json(checkpoint_path(directory))
        self.assertEqual(len(report["metrics"]["calls"]), case["max_llamadas"])
        self.assertEqual(report["estado"], "parcial")
        self.assertEqual(progress["tasks"][0]["status"], "interrumpida")
        self.assertEqual(progress["tasks"][0]["pending"]["Q04"], "Comprobar los scripts del repositorio.")
        self.assertEqual(progress["tasks"][1]["status"], "no_iniciada")
        answers = {a["id"]: a for a in report["cuestionario"]["respuestas"]}
        self.assertEqual(answers["Q04"]["respuesta"], "Resultado de Iris Q04")
        self.assertIn("Presupuesto global agotado", answers[case["pendiente"]]["pendiente"])

    def test_interrupted_process_leaves_completed_blocks_and_partial_answers_on_disk(self):
        snapshot, evidence = iris_fixture()
        calls = []

        def invoke(prompt, config):
            calls.append(config["task_id"])
            if len(calls) == 1:
                return response(comprobar=["Revisar el manifiesto."], cierre="Aplicación contrastada.", respuestas=[
                    answer(key, "F1:L1") for key in ("Q04", "Q05", "Q06", "Q07")])
            if len(calls) == 2:
                return response(comprobar=["Seguir las conexiones."], respuestas=[answer("Q08", "F1:L1")],
                                queries=[{"paths": ["src/client.py"]}])
            raise SystemExit

        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            with self.assertRaises(SystemExit):
                run_team(snapshot, directory, invoke=invoke, evidence=evidence)
            interrupt(directory)
            progress = read_json(checkpoint_path(directory))
        self.assertEqual(calls, ["aplicacion", "estructura", "estructura"])
        self.assertEqual(progress["tasks"][0]["status"], "completa")
        self.assertEqual(progress["tasks"][1]["status"], "interrumpida")
        answer_q08 = progress["tasks"][1]["answers"][0]
        self.assertEqual(answer_q08["respuesta"], "Resultado de Iris Q08")
        self.assertEqual(answer_q08["evidencia"][0]["path"], "package.json")
        self.assertIn("interrumpió", progress["tasks"][1]["pending"]["Q09"])
        self.assertIsNone(progress["active_task"])

    def test_provider_interruption_publishes_completed_answers_and_never_retries(self):
        snapshot, evidence = iris_fixture()
        calls = []

        def invoke(prompt, config):
            calls.append(config["task_id"])
            if len(calls) == 1:
                return response(comprobar=["Revisar el manifiesto."], cierre="Aplicación contrastada.", respuestas=[
                    answer(key, "F1:L1") for key in ("Q04", "Q05", "Q06", "Q07")])
            raise ProviderError("Interrupción simulada.")

        with tempfile.TemporaryDirectory() as folder:
            report = run_team(snapshot, Path(folder), invoke=invoke, evidence=evidence)
        self.assertEqual(calls, ["aplicacion", "estructura"])
        self.assertEqual(report["estado"], "parcial")
        answers = {a["id"]: a for a in report["cuestionario"]["respuestas"]}
        self.assertEqual(answers["Q04"]["evidencia"][0]["path"], "package.json")
        self.assertIn("Interrupción simulada", answers["Q08"]["pendiente"])
        self.assertIn("Interrupción simulada", render_markdown(report, snapshot))
