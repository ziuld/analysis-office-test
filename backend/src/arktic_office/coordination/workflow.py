"""Task workflows over Core's shared evidence, including Iris's synthesis."""
import json
import re
import time
import tomllib
from collections import Counter

from arktic_office.config.agents import FULL_STACK
from arktic_office.coordination.initial_sources import select
from arktic_office.core.errors import AuditError, SpecialistTimeout
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
OUTPUT = {"respuestas", "observaciones", "pendientes", "componentes", "conexiones", "controles", "dependencias"}


def load_tasks(folder=None, *, role=FULL_STACK):
    folder = folder or resource_path("profiles", "agents", role)
    questions = catalog() if role == FULL_STACK else catalog(role)
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
                raise AuditError("Configuración inválida en la tarea: " + task_id)
            if task_id == SYNTHESIS and (dependencies != seen or task["source_groups"]):
                raise AuditError("La síntesis de Iris depende de los bloques anteriores y usa sus resultados guardados.")
            seen.add(task_id)
            assigned_controls.update(controls)
            markdown = (folder / guide).read_text(encoding="utf-8").strip()
            entries = re.findall(r"^### (Q\d{2}) · (.+)$", markdown, re.MULTILINE) if role == FULL_STACK else [
                (key, expected[key]) for key in task["questions"]
            ]
            if not entries or any(expected.get(key) != wording for key, wording in entries):
                raise AuditError("Las preguntas de la tarea no coinciden con el catálogo de Core: " + task_id)
            if role != FULL_STACK:
                markdown += "\n\n" + "\n".join(f"### {key} · {wording}" for key, wording in entries)
            task.update(questions=[key for key, _ in entries], instructions=markdown)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AuditError("No se pudo cargar la definición de tareas de " + role + ".") from exc
    if (not tasks or (role == FULL_STACK and (tasks[-1]["id"] != SYNTHESIS or set(tasks[-1]["questions"]) != synthesis))
            or Counter(q for task in tasks for q in task["questions"]) != Counter(expected.keys())):
        raise AuditError("Flujo inválido: cada pregunta debe pertenecer a una tarea y la síntesis de Iris debe ser la última.")
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


def checkpoint_path(output, role=FULL_STACK):
    return output / "agents" / role / "workflow.json"


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


def interrupt(output, role=FULL_STACK):
    """Mark an interrupted checkpoint on service restart without calling a model."""
    path = checkpoint_path(output, role)
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


def receive(payload, task, questions, visible, source_ids, delivered_tools, *, role=FULL_STACK):
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
            if section == 'dependencias':
                from arktic_office.reporting.iris_delivery import triage
                decision = triage(item, visible, delivered_tools)
                if decision is None:
                    task['dependency_omissions'] = task.get('dependency_omissions',0) + 1
                    continue
                identity = tuple(decision[k] for k in ('package','version','advisory'))
                saved[:] = [old for old in saved if tuple(old[k] for k in ('package','version','advisory')) != identity]
                saved.append(decision)
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
    task["answers"], _ = assemble_answers(result.get("respuestas", []), role,
        lambda refs, _: locate(refs, visible), delivered_tools, questions=questions)
    received = {answer["id"] for answer in result.get("respuestas", [])}
    for answer in task["answers"]:
        if answer["id"] not in received:
            answer.update(respuesta="El agente no llegó a comprobar este punto.", pendiente="")
        if answer["estado"] in {"parcial", "no_comprobado"} and not answer["pendiente"]:
            task["pending"][answer["id"]] = "Comprobación en curso."
        elif answer["estado"] in {"parcial", "no_comprobado"}:
            task["pending"][answer["id"]] = answer["pendiente"]
        else:
            task["pending"].pop(answer["id"], None)


def research(snapshot, config, state, evidence, budget, output, cells, *, tasks=None, reserve_after=0):
    role = config["id"]
    is_iris = role == FULL_STACK
    if tasks is None:
        tasks = load_tasks() if is_iris else load_tasks(role=role)
    guides = {task["id"]: task["instructions"] for task in tasks}
    questions = {q["id"]: q for q in catalog(role)}
    progress = {"agent": role, "active_task": None, "stop_reason": None, "tasks": [], "sources": []}
    for spec in tasks:
        task = {**{k: v for k, v in spec.items() if k != "instructions"}, "status": "pendiente",
                "checks": [], "answers": [], "pending": {}, "result": {},
                "invocations": [], "retrievals": [], "originals": []}
        receive({}, task, [questions[q] for q in spec["questions"]], {}, {}, set(), role=role)
        progress["tasks"].append(task)
    path = checkpoint_path(output, role)
    limits = config["limits"]
    rounds = limits["research_rounds"]
    closing_reserve = limits.get("closure_reserve_seconds", 0)
    deadline = time.monotonic() + limits["seconds"]
    first_call = len(budget.calls)
    if is_iris:
        seeds, selection = select(role, evidence, limits, with_groups=True)
        seed_groups = {entry["path"]: entry["group"] for entry in selection["provided"]}
        seeds_by_task = {task["id"]: [f for f in seeds if seed_groups[f["path"]] in task["source_groups"]]
                         for task in tasks}
        retained = list(seeds)
    else:
        retained, seeds_by_task, selection = [], {}, {}
        for task in tasks:
            seeds, plan = select(role, evidence, limits, with_groups=True, groups=task["source_groups"])
            accepted = []
            for seed in seeds:
                candidate = {"files": list(retained)}
                evidence.retain(candidate, [seed])
                if (len(candidate["files"]) <= limits["files"]
                        and sum(len(f["text"].encode()) for f in candidate["files"]) <= limits["bytes"]):
                    retained = candidate["files"]
                    accepted.append(seed)
            seeds_by_task[task["id"]] = accepted
            selection[task["id"]] = {**plan, "provided": [item for item in plan["provided"]
                if any(seed["path"] == item["path"] for seed in accepted)],
                "bytes": sum(len(seed["text"].encode()) for seed in accepted)}
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
        files = list(seeds_by_task[task_id])
        prior_tasks = progress["tasks"][:n]
        previous = saved_answers(prior_tasks)
        known = source_index(supplied, source_ids)
        previous_context = {}
        last_lookup = []
        task_visible = {}
        delivered_tools = set()
        later = tasks[n + 1:]
        task_deadline = deadline - closing_reserve * len(later)
        available = available_rounds(task, later, rounds)
        if not is_iris:
            available = min(rounds, max(0, rounds - sum(t.get("reserved_rounds", 0) for t in later)),
                            max(0, budget.limits["calls"] - len(budget.calls) - 1 - reserve_after - len(later)))
            available = min(available, task["reserved_rounds"])
            previous_context["published_questions"] = config.get("knowledge_index", [])
        if task_id == SYNTHESIS:
            findings = [item for prior in prior_tasks for item in prior["result"].get("observaciones", [])]
            controls = [item for prior in prior_tasks for item in prior["result"].get("controles", [])]
            previous_context = {"respuestas": [answer_context(a) for a in previous.values()],
                                "observaciones": findings, "controles": controls,
                                "pendientes": [item for prior in prior_tasks for item in prior["result"].get("pendientes", [])]}
            labels = [label for item in findings + controls for label in item["evidencia"]]
            add_quotes(files, [ref for a in previous.values() for ref in a["evidencia"]] + locate(labels, known), evidence)
            delivered_tools.update(t for a in previous.values() for t in a["herramientas"])
        elif (task.get("controls") or not is_iris) and known:
            previous_context["source_index"] = prior_source_map(known, source_ids, evidence.graph)
        try:
            while True:
                now = time.monotonic()
                timeout = deadline - now
                if timeout <= 0:
                    if is_iris:
                        budget.stop_reason = "Tiempo total de Iris agotado. Quedan tareas por comprobar."
                    else:
                        stop_pending(progress, "Tiempo total del especialista agotado.")
                        break
                    raise AuditError(budget.stop_reason)
                task_time = task_deadline - now
                if closing_reserve and task_time <= 0:
                    close_task(task, "Sin margen para cerrar esta tarea dentro del plazo del especialista.",
                               "parcial" if task["originals"] else "no_iniciada")
                    break
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
                            'Empieza por la conclusión y cita de uno a tres tramos breves por afirmación cuando basten. '
                            'Los campos comprobar, cierre y queries amplían el objeto compacto. '
                            + "\nCONTEXTO DE TAREA NO CONFIABLE: " + json.dumps(context, ensure_ascii=False))
                if task.get("controls"):
                    message += "\nControles asignados a esta tarea: " + ", ".join(task["controls"]) + "."
                if "source_index" in previous_context:
                    message += ("\nEl índice de fuentes previas contiene ubicaciones y símbolos de otros bloques. "
                                'Recupera el tramo pertinente con "citations" antes de citarlo o usa "paths" y "start_line" para ampliarlo.')
                reserve_available = (not is_iris and getattr(budget, "shared_rounds", 0) > 0
                                     and budget.limits["calls"] - len(budget.calls) > 1 + reserve_after + len(later))
                time_allows_search = task_time >= 2 * closing_reserve
                can_search = (available or reserve_available) and time_allows_search
                if can_search:
                    message += (
                        f'\nQuedan {available} rondas asignadas para esta tarea. "queries" admite hasta 4 consultas por ronda. '
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
                    if reserve_available and not available:
                        message += ' Para pedir una ronda común añade "reserva" con la afirmación concreta que podría cerrarse.'
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
                call_deadline = task_deadline - (closing_reserve if can_search else 0)
                call_time = call_deadline - time.monotonic()
                if closing_reserve and call_time <= 0:
                    raise SpecialistTimeout("Se agotó el plazo local del especialista antes de iniciar otra llamada.")
                response = budget(message, {**config, "timeout": min(config["timeout"], call_time), "task_id": task_id,
                                            "timeout_scope": "specialist" if closing_reserve else "call",
                                            "context_sections": sections})
                invocation["usage"] = response.get("usage")
                invocation["duration_seconds"] = budget.calls[-1]["duration_seconds"]
                evidence.retain({"files": supplied}, files)
                evidence.retain(snapshot, files)
                known.update(visible)
                task_visible.update(visible)
                task["originals"].append(response["report"])
                try:
                    payload = json.loads(response["report"])
                except (ValueError, TypeError):
                    raise AuditError("El agente no devolvió JSON válido para la tarea.") from None
                if not isinstance(payload, dict):
                    raise AuditError("El agente no devolvió un objeto de tarea.")
                checks = payload.get("comprobar")
                if isinstance(checks, list):
                    task["checks"].extend(x for x in checks if isinstance(x, str) and x.strip() and x not in task["checks"])
                receive(payload, task, active_questions, task_visible, source_ids, delivered_tools, role=role)
                if role == "architecture" and "azure" in config["capabilities"] and isinstance(payload.get("propuesta_azure"), dict):
                    proposal = payload["propuesta_azure"]
                    refs = proposal.get("evidencia", [])
                    labels = [ref for ref in refs if isinstance(ref, str)] if isinstance(refs, list) else []
                    task["result"]["propuesta_azure"] = {**proposal, "evidencia": reference_labels(locate(labels, task_visible), source_ids)}
                write_json(path, progress)
                if not task["checks"]:
                    raise AuditError("El agente no registró qué necesitaba comprobar en esta tarea.")
                if not payload.get("queries"):
                    closure = payload.get("cierre")
                    if not isinstance(closure, str) or not closure.strip():
                        raise AuditError("El agente no explicó el cierre de esta tarea.")
                    close_task(task, closure)
                    break
                reserve = payload.get("reserva")
                if closing_reserve and not time_allows_search:
                    close_task(task, "Quedaron consultas pendientes al agotarse el margen de búsqueda.", "parcial")
                    break
                if not available and not (reserve_available and isinstance(reserve, str) and reserve.strip()):
                    raise AuditError("El agente pidió nuevas fuentes con las rondas de esta tarea agotadas.")
                if closing_reserve and task_deadline - time.monotonic() < closing_reserve:
                    # Keep the saved answers and use the remaining time to close with those sources.
                    continue
                if not is_iris:
                    files = []
                last_lookup, retained = lookup(payload["queries"], evidence, limits, retained, files,
                                                source_ids, known, previous)
                task["retrievals"].extend(last_lookup)
                state["retrievals"].extend(last_lookup)
                delivered_tools.update(entry["result"]["tool"] for entry in last_lookup if "tool" in entry["result"])
                if available:
                    available -= 1
                    rounds -= 1
                else:
                    budget.shared_rounds -= 1
                    task.setdefault("shared_rounds", []).append(reserve)
        except KeyboardInterrupt:
            budget.stop_reason = "La revisión se interrumpió. Se conservan los resultados ya guardados."
        except SpecialistTimeout as exc:
            stop_pending(progress, str(exc))
        except AuditError as exc:
            if not budget.stop_reason:
                close_task(task, redact(str(exc)), "parcial")
        if budget.stop_reason:
            stop_pending(progress, budget.stop_reason)
        else:
            progress["active_task"] = None
        write_json(path, progress)
        if budget.stop_reason or progress["stop_reason"]:
            break

    # Preserve the slot order used in all calls, including seeds that were never sent.
    supplied_by_path = {file["path"]: file for file in supplied}
    config["files"] = [supplied_by_path.get(path, {"path": path, "text": ""}) for path in source_ids]
    calls = budget.calls[first_call:]
    state.update(calls=len(calls), archivos=list(supplied_by_path),
                 bytes=sum(len(file["text"].encode()) for file in supplied),
                 task_states={task["id"]: task["status"] for task in progress["tasks"]})
    graph_locations = set()
    for retrieval in state["retrievals"]:
        for symbol in retrieval["result"].get("symbols", []):
            line = re.match(r"^L(\d+)", str(symbol.get("source_location", "")))
            path = symbol.get("source_file")
            if line and path in source_ids:
                graph_locations.add(f"{source_ids[path]}:L{line[1]}")
    state["observations_citing_graph_locations"] = sum(
        bool(graph_locations.intersection(item["evidencia"]))
        for task in progress["tasks"] for item in task["result"].get("observaciones", []))
    usages = [call.get("usage") for call in calls]
    if usages and all(isinstance(usage, dict) for usage in usages):
        state["usage"] = {key: sum(usage[key] for usage in usages) for key in set.intersection(*(set(u) for u in usages))
                          if all(type(usage[key]) in {int, float} for usage in usages)}
    result = {"observaciones": [], "respuestas": [], "pendientes": []}
    for task in progress["tasks"]:
        for section, items in task["result"].items():
            if section == 'dependencias':
                continue  # Stored in the workflow checkpoint; never force this into the legacy v3 schema.
            if section == "propuesta_azure":
                result[section] = items
            elif section != "respuestas":
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
            external = [q for q in query["questions"] if isinstance(q, str) and q not in previous]
            if external and getattr(evidence, "knowledge", None):
                result["published"] = evidence.respond({"questions": external})
        elif set(query) == {"citations"} and isinstance(query["citations"], list) and 1 <= len(query["citations"]) <= 12:
            refs = locate([ref for ref in query["citations"] if isinstance(ref, str)], known)
            result = {"citations": reference_labels(refs, source_ids)}
        else:
            result = {"error": "Consulta inválida de respuestas o citas guardadas."}
        add_quotes(files, refs, evidence)
        trace.append({"request": query, "result": result})
    return trace, retained
