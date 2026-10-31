"""One trusted role brief shared by research and analysis, without report schemas."""
import json
from arktic_office.resources.paths import resource_path


def instructions(role):
    common = resource_path("profiles", "agent-common.md").read_text(encoding="utf-8")
    if role == "coordinator":
        return common + "\nROL COORDINADOR: asigna objetivos a las especialidades y sintetiza sus aportaciones validadas. No selecciones archivos ni añadas hechos. Conserva certeza, condiciones, carencias y discrepancias; no generalices lo que un especialista no leyó como ausencia global.\n"
    agents = json.loads(resource_path("profiles", "agents.json").read_text(encoding="utf-8"))
    if role == 'security':
        role = 'backend-security'  # Compatibility for saved phase-2 contributions.
    agent = next(c for c in agents if c["id"] == role)
    return common + "\nRESPONSABILIDAD: " + agent["name"] + ". " + agent["focus"] + "\n" + "\n".join("- " + check for check in agent["checks"]) + "\n"
