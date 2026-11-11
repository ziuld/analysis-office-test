"""Iris reviews one report block at a time against Core's shared evidence."""
import json
import re
import time
import tomllib
from collections import Counter

from arktic_office.config.agents import FULL_STACK
from arktic_office.coordination.initial_sources import select
from arktic_office.core.errors import AuditError
from arktic_office.preparation.evidence import discovery_order
from arktic_office.preparation.lookups import source_ranges
from arktic_office.preparation.repository import redact
from arktic_office.reporting.deterministic import context as tool_context
from arktic_office.reporting.questionnaire import STATES, assemble_answers, catalog, complete
from arktic_office.reporting.references import locate
from arktic_office.reporting.security import CONTROLS
from arktic_office.reporting.specialist import prompt
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import read_json, write_json


SYNTHESIS = "alcance"
OUTPUT = {"respuestas", "observaciones", "pendientes", "componentes", "conexiones", "controles"}


def load_tasks(folder=None):
    folder = folder or resource_path("profiles", "agents", FULL_STACK)
    questions = catalog()
    expected = {q["id"]: q["pregunta"] for q in questions}
    synthesis = {q["id"] for q in questions if q["role"] == "coordinator"}
    try:
        tasks = tomllib.loads((folder / "workflow.toml").read_text(encoding="utf-8"))["tasks"]
        sources = tomllib.loads((folder / "initial-sources.toml").read_text(encoding="utf-8"))
        groups = {group["id"] for group in sources["groups"]}
        seen = set()
        assigned_controls = set()
        for task in tasks:
            task_id = task["id"]
            guide = task["guide"]
            dependencies = set(task.get("depends_on", []))
            controls = set(task.get("controls", []))
            reserved = task.get("reserved_rounds", 0)
            if (not re.fullmatch(r"[a-z][a-z0-9-]*", task_id) or task_id in seen
                    or not re.fullmatch(r"tasks/\d{2}-[a-z0-9-]+\.md", guide)
                    or not dependencies <= seen or set(task["source_groups"]) - groups
                    or not {"respuestas", "pendientes"} <= set(task["output"]) <= OUTPUT
                    or bool(controls) != ("controles" in task["output"])
                    or controls - CONTROLS.keys() or controls & assigned_controls
                    or type(reserved) is not int or reserved < 0):
                raise AuditError("Configuración inválida en la tarea de Iris: " + task_id)
            if task_id == SYNTHESIS and (dependencies != seen or task["source_groups"]):
                raise AuditError("La síntesis de Iris depende de los bloques anteriores y usa sus resultados guardados.")
            seen.add(task_id)
            assigned_controls.update(controls)
            markdown = (folder / guide).read_text(encoding="utf-8").strip()
            entries = re.findall(r"^### (Q\d{2}) · (.+)$", markdown, re.MULTILINE)
            if not entries or any(expected.get(key) != wording for key, wording in entries):
                raise AuditError("Las preguntas de la tarea no coinciden con el catálogo de Core: " + task_id)
            task.update(questions=[key for key, _ in entries], instructions=markdown)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AuditError("No se pudo cargar la definición de Iris.") from exc
    if (not tasks or tasks[-1]["id"] != SYNTHESIS or set(tasks[-1]["questions"]) != synthesis
            or Counter(q for task in tasks for q in task["questions"]) != Counter(expected.keys())):
        raise AuditError("Flujo de Iris inválido: cada pregunta debe pertenecer a una tarea y la síntesis debe ser la última.")
    return tasks


def available_rounds(task, later, remaining):
    """Reserve security lookups before distributing rounds to other tasks."""
    if task["id"] == SYNTHESIS:
        return 0
    reserved = task.get("reserved_rounds", 0)
    if reserved:
        priority_count = 1 + sum(bool(t.get("reserved_rounds")) for t in later)
        return min(reserved, (remaining + priority_count - 1) // priority_count)
    shared = max(0, remaining - sum(t.get("reserved_rounds", 0) for t in later))
    later_shared = sum(not t.get("reserved_rounds") and t["id"] != SYNTHESIS for t in later)
    return min(shared, max(1, shared - later_shared))


def checkpoint_path(output):
    return output / "agents" / FULL_STACK / "workflow.json"


def close_task(task, reason, status=None):
    for answer in task["answers"]:
        if answer["estado"] in {"parcial", "no_comprobado"} and not answer["pendiente"]:
            answer["pendiente"] = reason
    task.update(status=status or ("completa" if complete(task["answers"]) else "parcial"), closure_note=reason)
    task["pending"] = {a["id"]: a["pendiente"] for a in task["answers"] if a["estado"] in {"parcial", "no_comprobado"}}


def stop_pending(progress, reason):
    for task in progress["tasks"]:
        if task["status"] in {"pendiente", "en_curso"}:
            close_task(task, reason, "interrumpida" if task["status"] == "en_curso" else "no_iniciada")
    progress.update(active_task=None, stop_reason=reason)


def interrupt(output):
    """Mark an interrupted checkpoint on service restart without calling a model."""
    path = checkpoint_path(output)
    progress = read_json(path)
    if progress and any(task["status"] in {"pendiente", "en_curso"} for task in progress["tasks"]):
        stop_pending(progress, "La revisión se interrumpió al reiniciar el servicio. Resultado remoto desconocido.")
        write_json(path, progress)


def source_index(files, source_ids):
    return {f"{source_ids[file['path']]}:L{n}": {"path": file["path"], "line": n, "quote": line}
            for file in files for n, line in enumerate(file["text"].splitlines(), 1) if line.strip()}


def reference_labels(refs, source_ids):
    return [f"{source_ids[ref['path']]}:L{ref['line']}" for ref in refs]


def prior_source_map(known, source_ids, graph):
    """Share locations from previous tasks without resending their source text."""
    by_path = {}
    for ref in source_ranges(known.values()):
        path, start, end = ref["path"], ref["start_line"], ref["end_line"]
        entry = by_path.setdefault(path, {"path": path, "id": source_ids[path], "ranges": [], "symbols": []})
        if len(entry["ranges"]) < 3:
            entry["ranges"].append(f"L{start}" if start == end else f"L{start}-L{end}")
    for node in graph.get("nodes", []):
        path, label = node.get("source_file"), node.get("label")
        if path not in by_path or not isinstance(label, str) or not 1 <= len(label) <= 100:
            continue
        match = re.match(r"^L(\d+)", str(node.get("source_location", "")))
        if not match or f"{source_ids[path]}:L{match[1]}" not in known:
            continue
        symbols = by_path[path]["symbols"]
        symbol = {"name": label, "line": int(match[1])}
        if len(symbols) < 3 and symbol not in symbols:
            symbols.append(symbol)
    files, size = [], 0
    for path in sorted(by_path, key=lambda path: (discovery_order(path), path)):
        entry = by_path[path]
        length = len(json.dumps(entry, ensure_ascii=False).encode()) + 2
        if size + length <= 5000:
            files.append(entry)
            size += length
    return {"files": files, "omitted": len(by_path) - len(files)}


def saved_answers(tasks):
    return {answer["id"]: answer for task in tasks for answer in task["answers"]}


def answer_context(answer):
    # A previous answer is evidence for the current block, not a question to answer again.
    return {k: answer[k] for k in ("id", "estado", "respuesta", "pendiente", "referencias_originales", "herramientas")
            if k in answer}


def add_quotes(files, refs, evidence):
    by_path = {}
    for ref in refs:
        lines = by_path.setdefault(ref["path"], {})
        lines[ref["line"]] = ref["quote"]
    evidence.retain({"files": files}, [
        {"path": path, "text": "\n".join(lines.get(n, "") for n in range(1, max(lines) + 1)), "partial": True}
        for path, lines in by_path.items()])


def receive(payload, task, questions, visible, source_ids, delivered_tools):
    """Checkpoint representable contributions even when a turn also asks for sources."""
    result = task["result"]
    expected = {q["id"] for q in questions}
    answered = set()
    for section in task["output"]:
        values = payload.get(section, [])
        if not isinstance(values, list):
            continue
        saved = result.setdefault(section, [])
        key = {"respuestas": "id", "controles": "id", "componentes": "nombre"}.get(section)
        for item in values:
            if section == "pendientes":
                if isinstance(item, str) and item.strip() and item not in saved:
                    saved.append(item)
                continue
            if not isinstance(item, dict):
                continue
            if section == "controles" and item.get("id") not in task["controls"]:
                continue
            # Accept only citation labels delivered to this task. Resolve ranges here
            # so final composition cannot pick up lines supplied only to other blocks.
            refs = item.get("evidencia")
            refs = [ref for ref in refs if isinstance(ref, str)] if isinstance(refs, list) else []
            item = {**item, "evidencia": reference_labels(locate(refs, visible), source_ids)}
            if section == "respuestas":
                if (not isinstance(item.get("id"), str) or item["id"] not in expected - answered
                        or not isinstance(item.get("estado"), str) or item["estado"] not in STATES
                        or not isinstance(item.get("respuesta"), str) or not item["respuesta"].strip()):
                    continue
                answered.add(item["id"])
                tools = item.get("herramientas")
                item["herramientas"] = [t for t in tools if isinstance(t, str) and t in delivered_tools] if isinstance(tools, list) else []
                good = item.get("aspecto_favorable")
                if (not item["evidencia"] or not isinstance(good, dict)
                        or any(not isinstance(good.get(field), str) for field in ("titulo", "detalle"))):
                    item.pop("aspecto_favorable", None)
            if section == "observaciones" and item.get("tipo") not in ("vulnerabilidad", "coste", "operacion"):
                item.pop("tipo", None)
            if key and key in item:
                saved[:] = [previous for previous in saved if previous.get(key) != item[key]]
            if item not in saved:
                saved.append(item)
    task["answers"], _ = assemble_answers(result.get("respuestas", []), FULL_STACK,
        lambda refs, _: locate(refs, visible), delivered_tools, questions=questions)
    received = {answer["id"] for answer in result.get("respuestas", [])}
    for answer in task["answers"]:
        if answer["id"] not in received:
            answer.update(respuesta="Iris no llegó a comprobar este punto.", pendiente="")
        if answer["estado"] in {"parcial", "no_comprobado"} and not answer["pendiente"]:
            task["pending"][answer["id"]] = "Comprobación en curso."
        elif answer["estado"] in {"parcial", "no_comprobado"}:
            task["pending"][answer["id"]] = answer["pendiente"]
        else:
            task["pending"].pop(answer["id"], None)


def research(snapshot, config, state, evidence, budget, output, cells):
    tasks = load_tasks()
    guides = {task["id"]: task.pop("instructions") for task in tasks}
    questions = {q["id"]: q for q in catalog(FULL_STACK)}
    progress = {"agent": FULL_STACK, "active_task": None, "stop_reason": None, "tasks": [], "sources": []}
    for spec in tasks:
        task = {**spec, "status": "pendiente", "checks": [], "answers": [], "pending": {}, "result": {},
                "invocations": [], "retrievals": [], "originals": []}
        receive({}, task, [questions[q] for q in spec["questions"]], {}, {}, set())
        progress["tasks"].append(task)
    path = checkpoint_path(output)
    limits = config["limits"]
    rounds = limits["research_rounds"]
    started = time.monotonic()
    seeds, selection = select(FULL_STACK, evidence, limits, with_groups=True)
    seed_groups = {entry["path"]: entry["group"] for entry in selection["provided"]}
    retained = list(seeds)
    source_ids = {file["path"]: f"F{n}" for n, file in enumerate(retained, 1)}
    progress["source_ids"] = source_ids
    supplied = progress["sources"]
    tools = tool_context(snapshot)
    state.update(initial_sources=selection, invocations=[], retrievals=[], research_rounds=rounds)
    write_json(path, progress)

    for n, task in enumerate(progress["tasks"]):
        task_id = task["id"]
        progress["active_task"] = task_id
        task["status"] = "en_curso"
        active_questions = [questions[q] for q in task["questions"]]
        files = [file for file in seeds if seed_groups[file["path"]] in task["source_groups"]]
        prior_tasks = progress["tasks"][:n]
        previous = saved_answers(prior_tasks)
        known = source_index(supplied, source_ids)
        previous_context = {}
        last_lookup = []
        delivered_tools = set()
        available = available_rounds(task, tasks[n + 1:], rounds)
        if task_id == SYNTHESIS:
            findings = [item for prior in prior_tasks for item in prior["result"].get("observaciones", [])]
            controls = [item for prior in prior_tasks for item in prior["result"].get("controles", [])]
            previous_context = {"respuestas": [answer_context(a) for a in previous.values()],
                                "observaciones": findings, "controles": controls,
                                "pendientes": [item for prior in prior_tasks for item in prior["result"].get("pendientes", [])]}
            labels = [label for item in findings + controls for label in item["evidencia"]]
            add_quotes(files, [ref for a in previous.values() for ref in a["evidencia"]] + locate(labels, known), evidence)
            delivered_tools.update(t for a in previous.values() for t in a["herramientas"])
        elif task.get("controls") and known:
            previous_context["source_index"] = prior_source_map(known, source_ids, evidence.graph)
        try:
            while True:
                timeout = limits["seconds"] - (time.monotonic() - started)
                if timeout <= 0:
                    budget.stop_reason = "Tiempo total de Iris agotado. Quedan tareas por comprobar."
                    raise AuditError(budget.stop_reason)
                message = prompt({**snapshot, "files": files, "context_maps_managed": True}, config,
                                 task_guide=guides[task_id], source_ids=source_ids, sections=task["output"])
                context = {"repository": snapshot["repository"], "commit": snapshot["commit"],
                           "previous": previous_context, "lookup": last_lookup,
                           "checks": task["checks"],
                           "saved": [answer_context(a) for a in task["answers"] if "referencias_originales" in a]}
                if task_id != SYNTHESIS:
                    context["tools"] = tools
                message += ("\nEntrega solo estos campos de resultado: " + ", ".join(task["output"]) + "."
                            + ' En la primera respuesta registra qué necesitas comprobar en "comprobar" (lista breve de textos). '
                            'Para cerrar incluye "cierre" (texto concreto sobre el alcance y lo que falta). '
                            'Puedes entregar resultados parciales, con pendiente por pregunta, incluso junto con consultas. '
                            'No repitas resultados ya guardados salvo para actualizarlos. '
                            'Los campos comprobar, cierre y queries amplían el objeto compacto. '
                            + "\nCONTEXTO DE TAREA NO CONFIABLE: " + json.dumps(context, ensure_ascii=False))
                if task.get("controls"):
                    message += "\nControles asignados a esta tarea: " + ", ".join(task["controls"]) + "."
                if "source_index" in previous_context:
                    message += ("\nEl índice de fuentes previas contiene ubicaciones y símbolos de otros bloques. "
                                'Recupera el tramo pertinente con "citations" antes de citarlo o usa "paths" y "start_line" para ampliarlo.')
                if available:
                    message += (
                        f'\nQuedan {available} rondas para esta tarea. "queries" admite hasta 4 consultas por ronda. '
                        'Cada consulta admite como máximo 3 rutas en "paths" y 120 caracteres en "query". '
                        '"query" busca un símbolo o texto literal. Envía cada término en su propia consulta. '
                        'Ejemplo: [{"query":"authorize"},{"query":"sanitizeHtml"}]. '
                        '"paths" requiere rutas exactas de archivos, no directorios. Para descubrir un archivo busca el símbolo sin "paths". '
                        'Reparte 4 rutas en dos consultas de 3 y 1 dentro de la misma ronda. '
                        'Usa {"paths":["ruta"],"start_line":80} para un tramo (hasta 200 líneas), '
                        '{"query":"símbolo","paths":["ruta"]} para ubicar código, o {"list_paths":true,"offset":0} para inventario. '
                        'Sigue next_offset para paginar. Usa {"tool":"D04","index":true,"offset":0} para herramientas locales. '
                        'Puedes recuperar una respuesta previa con {"questions":["ID"]} o citas ya entregadas con '
                        '{"citations":["F2:L7","F3:L8-L10"]}. Usa las mismas referencias en el resultado.')
                else:
                    message += '\nCierra con los resultados disponibles y los pendientes. No hay rondas de consulta para esta llamada.'
                visible = source_index(files, source_ids)
                sections = {"source_bytes": sum(len(ref["quote"].encode()) for ref in visible.values()),
                            "repeated_source_bytes": sum(len(ref["quote"].encode()) for key, ref in visible.items() if key in known),
                            "previous_results_bytes": len(json.dumps(previous_context, ensure_ascii=False).encode()),
                            "lookup_bytes": len(json.dumps(last_lookup, ensure_ascii=False).encode())}
                invocation = {"task": task_id, "stage": "synthesis" if task_id == SYNTHESIS else "analysis",
                              "prompt_bytes": len(message.encode()), "context_sections": sections, "usage": None}
                task["invocations"].append(invocation)
                state["invocations"].append(invocation)
                write_json(path, progress)
                write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
                response = budget(message, {**config, "timeout": min(config["timeout"], timeout), "task_id": task_id,
                                            "context_sections": sections})
                invocation["usage"] = response.get("usage")
                invocation["duration_seconds"] = budget.calls[-1]["duration_seconds"]
                evidence.retain({"files": supplied}, files)
                evidence.retain(snapshot, files)
                known.update(visible)
                task["originals"].append(response["report"])
                try:
                    payload = json.loads(response["report"])
                except (ValueError, TypeError):
                    raise AuditError("Iris no devolvió JSON válido para la tarea.") from None
                if not isinstance(payload, dict):
                    raise AuditError("Iris no devolvió un objeto de tarea.")
                checks = payload.get("comprobar")
                if isinstance(checks, list):
                    task["checks"].extend(x for x in checks if isinstance(x, str) and x.strip() and x not in task["checks"])
                receive(payload, task, active_questions, visible, source_ids, delivered_tools)
                write_json(path, progress)
                if not task["checks"]:
                    raise AuditError("Iris no registró qué necesitaba comprobar en esta tarea.")
                if not payload.get("queries"):
                    closure = payload.get("cierre")
                    if not isinstance(closure, str) or not closure.strip():
                        raise AuditError("Iris no explicó el cierre de esta tarea.")
                    close_task(task, closure)
                    break
                if available <= 0:
                    raise AuditError("Iris pidió nuevas fuentes con las rondas de esta tarea agotadas.")
                last_lookup, retained = lookup(payload["queries"], evidence, limits, retained, files,
                                                source_ids, known, previous)
                task["retrievals"].extend(last_lookup)
                state["retrievals"].extend(last_lookup)
                delivered_tools.update(entry["result"]["tool"] for entry in last_lookup if "tool" in entry["result"])
                available -= 1
                rounds -= 1
        except KeyboardInterrupt:
            budget.stop_reason = "La revisión de Iris se interrumpió. Se conservan los resultados ya guardados."
        except AuditError as exc:
            if not budget.stop_reason:
                close_task(task, redact(str(exc)), "parcial")
        if budget.stop_reason:
            stop_pending(progress, budget.stop_reason)
        else:
            progress["active_task"] = None
        write_json(path, progress)
        if budget.stop_reason:
            break

    # Preserve the slot order used in all calls, including seeds that were never sent.
    supplied_by_path = {file["path"]: file for file in supplied}
    config["files"] = [supplied_by_path.get(path, {"path": path, "text": ""}) for path in source_ids]
    state.update(calls=len(budget.calls), archivos=list(supplied_by_path),
                 bytes=sum(len(file["text"].encode()) for file in supplied),
                 task_states={task["id"]: task["status"] for task in progress["tasks"]})
    usages = [call.get("usage") for call in budget.calls]
    if usages and all(isinstance(usage, dict) for usage in usages):
        state["usage"] = {key: sum(usage[key] for usage in usages) for key in set.intersection(*(set(u) for u in usages))
                          if all(type(usage[key]) in {int, float} for usage in usages)}
    result = {"observaciones": [], "respuestas": [], "pendientes": []}
    for task in progress["tasks"]:
        for section, items in task["result"].items():
            if section != "respuestas":
                result.setdefault(section, []).extend(items)
        for answer in task["answers"]:
            result["respuestas"].append({k: answer[k] for k in ("id", "estado", "respuesta", "pendiente", "herramientas")} |
                {"evidencia": reference_labels(answer["evidencia"], source_ids)} |
                ({"aspecto_favorable": answer["aspecto_favorable"]} if "aspecto_favorable" in answer else {}))
    originals = [{"tarea": task["id"], "respuestas_originales": task["originals"]}
                 for task in progress["tasks"] if task["originals"]]
    return {"report": json.dumps(result, ensure_ascii=False), "original": json.dumps(originals, ensure_ascii=False, indent=2)}


def lookup(queries, evidence, limits, retained, files, source_ids, known, previous):
    if not isinstance(queries, list) or not 1 <= len(queries) <= 4:
        raise AuditError("Una ronda admite entre una y cuatro consultas.")
    trace = []
    regular = [q for q in queries if not isinstance(q, dict) or not ({"questions", "citations"} & q.keys())]
    if regular:
        retained, trace = evidence.batch(regular, limits, initial=retained, max_queries=4 - len(queries) + len(regular),
                                         strict=True)
        by_path = {file["path"]: file for file in retained}
        for path in by_path:
            source_ids.setdefault(path, f"F{len(source_ids) + 1}")
        for entry in trace:
            for window in entry["result"]["fragments"]:
                file = by_path[window["path"]]
                start = window["start"] - 1
                text = "\n".join([""] * start + file["text"].splitlines()[start:window["end"]])
                evidence.retain({"files": files}, [{**window, "text": text}])
    for query in queries:
        if not isinstance(query, dict) or not ({"questions", "citations"} & query.keys()):
            continue
        refs = []
        if set(query) == {"questions"} and isinstance(query["questions"], list) and 1 <= len(query["questions"]) <= 4:
            answers = [previous[q] for q in query["questions"] if isinstance(q, str) and q in previous]
            refs = [ref for answer in answers for ref in answer["evidencia"]]
            result = {"answers": [answer_context(answer) for answer in answers]}
        elif set(query) == {"citations"} and isinstance(query["citations"], list) and 1 <= len(query["citations"]) <= 12:
            refs = locate([ref for ref in query["citations"] if isinstance(ref, str)], known)
            result = {"citations": reference_labels(refs, source_ids)}
        else:
            result = {"error": "Consulta inválida de respuestas o citas guardadas."}
        add_quotes(files, refs, evidence)
        trace.append({"request": query, "result": result})
    return trace, retained
