"""Local UI fixture: no GitHub, scanner or model access. Does not replace historical reports."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "auditor"))
from team import run_team, write_json
from outcome import INSUFFICIENT
from executive import render_html, render_markdown


def main():
    default_root = Path("/reports") if Path("/reports").is_dir() else Path(__file__).resolve().parents[1] / "reports"
    root = Path(os.environ.get("AUDIT_REPORTS_DIR", str(default_root)))
    output = root / "demo-informacion-insuficiente"
    if output.exists():
        raise SystemExit("El ejemplo ya existe; no se reemplaza automáticamente.")
    output.mkdir(parents=True)
    snapshot = {"repository": "https://github.com/arktic/ejemplo-simulado", "project_name": "Ejemplo: información insuficiente",
                "branch": "main", "commit": "0" * 40, "simulation": True,
                "evidence_origin": "SIMULACIÓN de falta de información; respuestas controladas, sin agentes ni llamadas al modelo.",
                "files": [{"path": "routes.py", "text": "# Ejemplo sin implementación disponible."}], "excluded": [], "bytes_read": 40}
    report = {"schema_version": 3, "confirmados": [], "indicios": [], "controles": [], "dudas": [],
              "evaluacion": {"estado": INSUFFICIENT, "motivo": "No recibí implementación suficiente para evaluar esta especialidad.",
                             "necesita": ["Código de las rutas y controladores que procesan las solicitudes.", "Dependencias y configuración de arranque y base de datos."]}}
    data = run_team(snapshot, output, invoke=lambda *args: {"report": json.dumps(report), "usage": {"api_calls": 0, "total_tokens": 0}}, emit=lambda *args, **kwargs: None)
    for cell in data["celulas"]:
        cell.update(provider="simulacion", model="sin_modelo", reasoning="no_aplica")
    write_json(output / "evidencia.json", snapshot)
    write_json(output / "informe.json", data)
    write_json(output / "estado.json", {"estado": data["estado"], "celulas": data["celulas"]})
    for cell in data["celulas"]:
        path = output / "celulas" / (cell["id"] + ".json")
        original = json.loads(path.read_text(encoding="utf-8"))
        write_json(path, {**original, **cell})
    (output / "informe.html").write_text(render_html(data, snapshot), encoding="utf-8")
    (output / "informe.md").write_text(render_markdown(data, snapshot), encoding="utf-8")
    print("Ejemplo local creado: " + str(output))


if __name__ == "__main__":
    main()
