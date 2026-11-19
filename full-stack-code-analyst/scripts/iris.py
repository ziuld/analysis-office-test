"""Portable Iris local preparation and cache. Analysis stays in the invoking chat."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True

from storage import (KIT, LOCAL, digest, file_hash, intact, inventory, locked, now,
                     local_path, require_project, profile_hash, read_json, write_json)
from scanners import VERSIONS, cached, run_tool, selected_files, signature, tool_info
import review_evidence
import semgrep_docker
import report_renderer

AGENT_VERSION = (KIT / "VERSION").read_text(encoding="utf-8").strip()


def revisions():
    directory = LOCAL / "revisiones"
    return sorted(directory.glob("*/estado.json"), key=lambda path: path.stat().st_mtime, reverse=True)


def status(source, tools):
    reusable = []
    for path in revisions():
        state = read_json(path, {})
        if (state.get("source", {}).get("identity") == source["identity"]
                and state.get("source", {}).get("profile") == source["profile"]
                and state.get("status") == "complete" and intact(path.parent, state)):
            tool_states = state.get("tools", {})
            consistent = True
            for name, info in tool_states.items():
                if info.get("status") != "complete":
                    if (info.get("status") in {"missing", "unavailable", "needs_network_consent", "needs_image_download"}
                            and tools[name]["status"] == "available"):
                        consistent = False
                    continue
                _, current, usable, _ = cached(name, source, tools[name])
                if (not usable or info.get("key") != current.get("key")
                        or info.get("artifacts", {}).get("resultado.json") != current.get("artifacts", {}).get("resultado.json")):
                    consistent = False
            if consistent:
                reusable.append({"agent_version": state.get("agent_version"),
                                 "provenance": state.get("provenance", {"mode": "unrecorded"}),
                                 "semgrep_engine": state.get("semgrep_engine", "local"),
                                 "review": str(path.parent), "report": str(path.parent / "informe-iris.html"),
                                 "interpretation": state.get("interpretation"), "selected_tools": list(tool_states), "tools": {
                                     name: {"status": value.get("status"), "finished_at": value.get("finished_at")}
                                     for name, value in tool_states.items()}})
    available = {}
    for name, info in tools.items():
        folder, state, usable, stale = cached(name, source, info)
        available[name] = {**info, "cached": usable, "stale": stale,
                           "input_count": len(selected_files(name, source)),
                           "result": str(folder / "resultado.json") if usable else None,
                           "queried_at": state.get("finished_at")}
    excluded = [item for item in source["files"] if item["kind"] != "text"]
    return {"agent_version": AGENT_VERSION,
            "source": {key: source[key] for key in ("root", "identity", "branch", "commit", "scope", "exclusions")},
            "files": len(source["files"]), "profile": source["profile"],
            "excluded": {"counts": dict(Counter(item["kind"] for item in excluded)),
                         "examples": [item["path"] for item in excluded[:20]]},
            "tools": available, "reusable_reports": reusable}


def resolve_review(value):
    path = Path(value).resolve(strict=True)
    parent = (LOCAL / "revisiones").resolve()
    if path.parent != parent or path.is_symlink():
        raise ValueError("La revisión debe estar directamente dentro de .local/revisiones/.")
    if not (path / "estado.json").is_file():
        raise ValueError("No existe el estado de esa revisión.")
    local_path(path)
    state = read_json(path / 'estado.json', {})
    require_project(Path(state['source']['root']))
    return path


def prepare(args, source, tools):
    selected = args.tools.split(",") if args.tools else []
    if len(set(selected)) != len(selected) or set(selected) - VERSIONS.keys():
        raise ValueError("Lista de herramientas inválida.")
    refresh = set(args.refresh.split(",")) if args.refresh else set()
    if refresh - set(selected):
        raise ValueError("--refresh debe nombrar herramientas seleccionadas.")
    mode = args.mode
    base_folder = resolve_review(args.base_review) if args.base_review else None
    base = read_json(base_folder / "estado.json", {}) if base_folder else None
    if mode == "extend" and not base:
        raise ValueError("Una ampliación requiere --base-review.")
    if mode != "extend" and base:
        raise ValueError("Solo el modo extend admite una revisión base.")
    if mode == "independent" and not args.fresh_context:
        raise ValueError("La evaluación independiente requiere un chat sin antecedentes y --fresh-context.")
    if args.fresh_context and mode != "independent":
        raise ValueError("--fresh-context se usa solo con --mode independent.")
    if base and (base.get("status") != "complete" or not intact(base_folder, base)
                 or base.get("source", {}).get("root") != source["root"]):
        raise ValueError("La base debe ser una revisión íntegra del mismo proyecto.")
    previous = status(source, tools)
    compatible = [item for item in previous["reusable_reports"]
                  if set(item["selected_tools"]) == set(selected) and item["interpretation"] == args.interpretation
                  and ("semgrep" not in selected or item["semgrep_engine"] == args.semgrep_engine)]
    if compatible and mode == "new" and not refresh and not args.force_review:
        return {"action": "reuse_report", **compatible[0]}
    identifier = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    folder = LOCAL / "revisiones" / identifier
    folder.mkdir(parents=True)
    state = {"schema_version": 1, "agent_version": AGENT_VERSION,
             "status": "preparing", "created_at": now(), "source": source,
             "tools": {}, "interpretation": args.interpretation, "blocks": [],
             "semgrep_engine": args.semgrep_engine if "semgrep" in selected else None,
             "provenance": {"mode": mode, "base_review": str(base_folder) if base_folder else None,
                            "base_state_hash": file_hash(base_folder / "estado.json") if base_folder else None,
                            "fresh_context_declared": bool(args.fresh_context)}}
    write_json(folder / "estado.json", state)
    write_json(folder / "entrada/inventario.json", source)
    for tool in selected:
        kwargs = {"semgrep_engine": args.semgrep_engine, "allow_image_download": args.allow_image_download} if tool == "semgrep" else {}
        result = run_tool(tool, source, refresh=tool in refresh, online=args.online, **kwargs)
        state["tools"][tool] = result
        output = folder / tool
        output.mkdir()
        write_json(output / "estado.json", result)
        state["status"] = "preparing"
        write_json(folder / "estado.json", state)
    if inventory(Path(source["root"]), source.get("exclusions", []))["identity"] != source["identity"]:
        state["status"] = "source_changed"
        write_json(folder / "estado.json", state)
        raise ValueError("El proyecto cambió durante la preparación. Repite status y prepare.")
    state["status"] = "ready_for_chat"
    review_evidence.initialize(folder, state, base)
    report_renderer.initialize(folder, state)
    state['renderer'] = 'canonical-json-v1'
    write_json(folder / "estado.json", state)
    return {"action": "review_in_current_chat", "agent_version": AGENT_VERSION,
            "review": str(folder), "report": str(folder / "informe-iris.html"),
            "source": previous["source"], "tools": state["tools"], "provenance": state["provenance"],
            "evidence_files": ["informe.json", "cobertura.json", "dependencias.json", "hallazgos.json", "cambios-entrada.json"]}


class Report(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.sources = []
        self.code = False
        self.references = []

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if "id" in values:
            self.ids.append(values["id"])
        if "href" in values:
            self.links.append(values["href"])
        if "src" in values:
            self.sources.append(values["src"])
        if tag == "code":
            self.code = True

    def handle_endtag(self, tag):
        if tag == "code":
            self.code = False

    def handle_data(self, data):
        if self.code:
            match = re.fullmatch(r"(.+):(\d+)(?:-(\d+))?", data.strip())
            if match:
                self.references.append(match.groups())


def validate_report(path, source):
    html = path.read_text(encoding="utf-8")
    parsed = Report()
    parsed.feed(html)
    if len(parsed.ids) != len(set(parsed.ids)):
        raise ValueError("El HTML contiene identificadores duplicados.")
    if {key for key in parsed.ids if re.fullmatch(r"Q\d{2}", key)} != {f"Q{i:02}" for i in range(1, 41)}:
        raise ValueError("El HTML debe contener Q01–Q40 una vez cada una.")
    if [key for key in parsed.ids if key.startswith("bloque-")] != [f"bloque-{i:02}" for i in range(1, 8)]:
        raise ValueError("Los siete bloques deben aparecer en su orden.")
    if re.search(r"{{[A-Z]+}}", html):
        raise ValueError("Quedan marcadores de plantilla sin rellenar.")
    if any(not link.startswith("#") or link[1:] not in parsed.ids for link in parsed.links):
        raise ValueError("Hay enlaces externos o destinos internos sin resolver.")
    if not parsed.sources or any(not target.startswith("data:") for target in parsed.sources):
        raise ValueError("El HTML debe llevar sus recursos embebidos.")
    template = (KIT / "plantillas/informe.html").read_text(encoding="utf-8")
    for tag in ("style", "script"):
        pattern = rf"<{tag}\b[^>]*>(.*?)</{tag}>"
        if re.findall(pattern, html, re.S) != re.findall(pattern, template, re.S):
            raise ValueError("Los estilos o la navegación difieren de la plantilla.")
    root = Path(source["root"])
    for name, start, end in parsed.references:
        target = (root / name).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError("Una referencia del HTML no pertenece al proyecto.")
        if not 1 <= int(start) <= int(end or start) <= len(target.read_text(encoding="utf-8-sig").splitlines()):
            raise ValueError("Una referencia del HTML tiene un rango de líneas inválido.")
    return {"questions": 40, "blocks": 7, "citation_ranges_checked": len(parsed.references),
            "limitation": "Valida estructura y rangos; Iris contrasta la evidencia semántica en el chat."}


def finish(args):
    folder = resolve_review(args.review)
    state = read_json(folder / "estado.json", {})
    source = inventory(Path(state["source"]["root"]), state["source"].get("exclusions", []))
    if source["identity"] != state["source"]["identity"] or source["profile"] != state["source"]["profile"]:
        raise ValueError("Cambió el código o las instrucciones. Inicia una nueva revisión.")
    if state.get("status") not in {"ready_for_chat", "complete"}:
        raise ValueError("Esta revisión no está preparada para publicar.")
    report = folder / "informe-iris.html"
    block_files = [folder / "bloques" / f"{number:02}.md" for number in range(1, 8)]
    if any(not path.is_file() or not path.read_text(encoding="utf-8").strip() for path in block_files):
        raise ValueError("Guarda las siete fichas en bloques/01.md a bloques/07.md antes de finalizar.")
    validation = validate_report(report, source)
    if state.get('renderer') == 'canonical-json-v1':
        canonical, fichas = report_renderer.build(folder, state)
        if report.read_text(encoding='utf8') != canonical:
            raise ValueError('El HTML no coincide con el generador fijo. Ejecuta render; no lo edites a mano.')
        if any((folder / 'bloques' / name).read_text(encoding='utf8') != value for name, value in fichas.items()):
            raise ValueError('Las fichas no coinciden con los datos. Ejecuta render.')
        validation['renderer'] = 'canonical-json-v1'
    if state.get("provenance"):
        fragment = review_evidence.render(folder, state)
        if fragment not in report.read_text(encoding="utf8"):
            raise ValueError("Inserta evidencia.html actualizado en los anexos del informe antes de finalizar.")
        coverage, _, dependencies = review_evidence.load(folder, state)
        if args.coverage == "complete" and (
            any(b["state"] != "reviewed" for b in coverage)
            or any(t.get("status") != "complete" for t in state["tools"].values())
            or any(row["decision"] == "pending" for row in dependencies)):
            raise ValueError("Hay cobertura o herramientas pendientes; finaliza con --coverage partial.")
    state.update(status="complete", finished_at=now(), author=args.author or "modelo de la sesión actual",
                 validation=validation, coverage=args.coverage)
    state["blocks"] = [path.relative_to(folder).as_posix() for path in block_files]
    state["artifacts"] = {"informe-iris.html": file_hash(report),
                          **{path.relative_to(folder).as_posix(): file_hash(path) for path in block_files}}
    if state.get("provenance"):
        for name in ("cobertura.json", "dependencias.json", "hallazgos.json", "comparacion.json", "evidencia.html", "cambios-entrada.json"):
            state["artifacts"][name] = file_hash(folder / name)
    if state.get('renderer') == 'canonical-json-v1':
        state['artifacts']['informe.json'] = file_hash(folder / 'informe.json')
    write_json(folder / "estado.json", state)
    return {"report": str(report), "agent_version": state.get("agent_version"),
            "coverage": args.coverage, "validation": validation}


def results(args):
    folder = resolve_review(args.review)
    state = read_json(folder / "estado.json", {})
    result = state.get("tools", {}).get(args.tool, {})
    base = Path(result.get("folder", ""))
    if not base.resolve().is_relative_to((LOCAL / "cache").resolve()):
        raise ValueError("No hay un resultado local para esa herramienta.")
    payload = read_json(base / "resultado.json")
    if payload is None:
        return {"status": result.get("status"), "error": result.get("error")}
    if result.get("status") == "complete" and not intact(base, result):
        raise ValueError("El resultado de la herramienta cambió. Repite la preparación antes de consultarlo.")
    if args.tool == "graphify":
        items = payload.get("nodes", [])
    elif args.tool == "gitleaks":
        items = payload if isinstance(payload, list) else payload.get("findings", [])
    elif args.tool == "semgrep":
        items = payload.get("results", [])
    else:
        items = []
        for result in payload.get("results", []):
            for package in result.get("packages", []):
                items.append({"source": result.get("source"), "package": package.get("package"),
                              "vulnerabilities": [{"id": advisory.get("id"), "summary": advisory.get("summary"),
                                                   "aliases": advisory.get("aliases", [])}
                                                  for advisory in package.get("vulnerabilities", [])]})
    if args.search:
        items = [item for item in items if args.search.casefold() in json.dumps(item, ensure_ascii=False).casefold()]
    return {"status": result.get("status"), "total": len(items), "offset": args.offset,
            "items": items[args.offset:args.offset + args.limit],
            "next_offset": args.offset + args.limit if args.offset + args.limit < len(items) else None,
            "result_file": str(base / "resultado.json"), "queried_at": result.get("finished_at")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"Iris {AGENT_VERSION}")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "prepare"):
        sub = subs.add_parser(name)
        sub.add_argument("--project", type=Path, required=True)
        sub.add_argument("--exclude", action="append", default=[], help="Ruta relativa de archivo/carpeta fuera del alcance; repetible")
        sub.add_argument("--semgrep-engine", choices=("local", "docker", "skip"), default="local")
        if name == "prepare":
            sub.add_argument("--tools", default="graphify,gitleaks,semgrep,osv")
            sub.add_argument("--online", action="store_true", help="Autoriza consultas OSV de metadatos")
            sub.add_argument("--refresh", default="", help="Herramientas a recalcular, separadas por coma")
            sub.add_argument("--force-review", action="store_true")
            sub.add_argument("--interpretation", choices=("standard", "deep"), default="deep")
            sub.add_argument("--mode", choices=("new", "extend", "independent"), default="new")
            sub.add_argument("--base-review")
            sub.add_argument("--fresh-context", action="store_true", help="Declaración del ejecutor: chat sin antecedentes")
            sub.add_argument("--allow-image-download", action="store_true", help="Autoriza descargar la imagen Semgrep si falta")
    sub = subs.add_parser("evidence")
    sub.add_argument("--review", required=True)
    sub = subs.add_parser('render')
    sub.add_argument('--review', required=True)
    sub = subs.add_parser("install")
    sub.add_argument("tool", choices=list(VERSIONS))
    sub = subs.add_parser("results")
    sub.add_argument("--review", required=True)
    sub.add_argument("--tool", choices=list(VERSIONS), required=True)
    sub.add_argument("--search", default="")
    sub.add_argument("--offset", type=int, default=0)
    sub.add_argument("--limit", type=int, default=10)
    sub = subs.add_parser("finish")
    sub.add_argument("--review", required=True)
    sub.add_argument("--author")
    sub.add_argument("--coverage", choices=("partial", "complete"), default="partial")
    sub = subs.add_parser("export")
    sub.add_argument("--review", required=True)
    sub.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command in {'status', 'prepare'}:
            require_project(args.project)
        elif args.command in {'render', 'evidence', 'finish', 'results', 'export'}:
            resolve_review(args.review)
        if args.command == "results" and (args.offset < 0 or not 1 <= args.limit <= 50):
            raise ValueError("Usa offset positivo y un límite de 1 a 50.")
        with locked():
            if args.command in {"status", "prepare"}:
                source = inventory(args.project, args.exclude)
                tools = {name: tool_info(name) for name in VERSIONS}
                if args.semgrep_engine == "docker":
                    tools["semgrep"] = semgrep_docker.info()
                elif args.semgrep_engine == "skip":
                    tools["semgrep"] = {"status": "skipped", "engine": "skip"}
                result = status(source, tools) if args.command == "status" else prepare(args, source, tools)
                if args.command == "status":
                    result["semgrep_options"] = {"local": tool_info("semgrep"), "docker": semgrep_docker.probe()}
            elif args.command == "install":
                from install_tools import install
                result = install(args.tool)
            elif args.command == "finish":
                result = finish(args)
            elif args.command == "results":
                result = results(args)
            elif args.command == "evidence":
                folder = resolve_review(args.review)
                state = read_json(folder / "estado.json", {})
                if state.get("status") != "ready_for_chat":
                    raise ValueError("Solo se puede generar evidencia para una revisión abierta.")
                fragment = review_evidence.render(folder, state)
                result = {"evidence": str(folder / "evidencia.html"), "characters": len(fragment),
                          "instruction": "El comando render incorpora estos anexos automáticamente."}
            elif args.command == 'render':
                folder = resolve_review(args.review)
                state = read_json(folder / 'estado.json', {})
                if state.get('status') != 'ready_for_chat' or state.get('renderer') != 'canonical-json-v1':
                    raise ValueError('render requiere una revisión abierta preparada con el generador fijo.')
                report_renderer.render(folder, state)
                validation = validate_report(folder / 'informe-iris.html', state['source'])
                result = {'report': str(folder / 'informe-iris.html'), 'validation': validation}
            else:
                folder = resolve_review(args.review)
                state = read_json(folder / "estado.json", {})
                if state.get("status") != "complete" or not intact(folder, state):
                    raise ValueError("El informe debe estar finalizado e íntegro antes de exportar.")
                target = local_path(args.output.resolve())
                if target.suffix.lower() not in {".html", ".htm"}:
                    raise ValueError("La copia del informe debe tener extensión .html o .htm.")
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as destination, (folder / "informe-iris.html").open("rb") as origin:
                    shutil.copyfileobj(origin, destination)
                exports = read_json(LOCAL / "exports.json", [])
                if str(target) not in exports:
                    exports.append(str(target))
                    write_json(LOCAL / "exports.json", exports)
                result = {"exported": str(target)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except PermissionError as exc:
        print(json.dumps({'error': str(exc), 'error_code': 'permission_required', 'required_path': str(LOCAL),
                          'action': 'Solicita permiso de escritura y reintenta en la misma carpeta del agente.',
                          'fallback_allowed': False}, ensure_ascii=False), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
