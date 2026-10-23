"""Read the shared editorial standard at prompt construction time."""
import re
import json
import hashlib
from arktic_office.resources.paths import standard_path
from arktic_office.preparation.repository import AuditError


def sections():
    source = standard_path().read_text(encoding="utf-8")
    parts = re.split(r"^## (.+)\s*$", source, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}

def instructions(cell_id=None):
    names = {"security": "Seguridad", "architecture": "Arquitectura", "inventory": "Inventario"}
    content = sections()
    selected = ["Común", names.get(cell_id, "Consolidación")]
    return "ESTÁNDAR EDITORIAL COMPARTIDO · versión 1\n" + "\n\n".join("## " + name + "\n" + content[name] for name in selected)

def contract(cell_id):
    if cell_id == "inventory":
        sample = {"resumen": {"descripcion": "Qué hace, solo si está documentado", "tecnologia_principal": "Tecnología principal declarada", "evidencia": ["F1:L7"]}}
    elif cell_id == "architecture":
        sample = {"flujo_actual": {"componentes": [{"id": "app", "nombre": "Aplicación", "descripcion": "Función observada", "evidencia": ["F1:L7"]}], "conexiones": []}, "estado_operativo": [{"aspecto": "capacidad", "estado": "no_evaluado", "descripcion": "No hay mediciones aportadas", "pendiente": "Qué medir", "evidencia": []}], "decision": {"propuesta": "Qué se propone decidir", "evidencia_pendiente": ["Qué falta aportar"], "siguiente_paso": "Acción para revisión humana"}}
    else:
        return ""
    return "\nAñade presentacion a la raíz del JSON. Solo bloques de tu célula; adapta los valores y fuentes, no copies el ejemplo: " + json.dumps(sample, ensure_ascii=False) + "\nLos bloques sin evidencia se omiten; no fabriques un resumen ni nodos sin fuentes. Estado operativo: observado/indicio/no_evaluado; conexiones: observada/inferida/desconocida.\n"

def metadata():
    instructions()  # Require the shared consolidation section to be installed.
    return {"version": 1, "archivo": "docs/ESTANDAR_COMUNICACION_INFORMES.md", "sha256": hashlib.sha256(standard_path().read_bytes()).hexdigest()}
