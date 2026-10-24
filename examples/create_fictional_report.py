"""Render a hand-written fictional scenario. No network, scanners or model calls."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
from arktic_office.reporting.executive import render_html
from arktic_office.reporting.reports import markdown, validate_report
from arktic_office.coordination.team import consolidate
from arktic_office.reporting.security import CONTROLS

RUN_ID = "demo-editorial-v12-portal-personal"
SOURCES = {
    "README.demo.md": "EJEMPLO FICTICIO; no es el proyecto real.\nPortal para registrar asistencia, ausencias y tareas de personal junior.\nGuarda nombres, correo corporativo, horarios y observaciones internas.\nArranque: Docker Compose para PostgreSQL; npm run dev para web y API.\nEl equipo de negocio mantiene el ordenador encendido.\nAcceso remoto mediante túnel a http://localhost:5173.\nNo se aportan procedimientos de copia, recuperación ni responsables de operación.",
    "api/server.demo.js": "// Pseudocódigo ficticio, no ejecutar.\nconst app = express();\napp.use(express.json());\napp.get('/api/personal', async (req,res) => {\n  const rows = await db.query('SELECT * FROM personal');\n  res.json(rows);\n});\napp.post('/api/admin/borrar', async (req,res) => {\n  if (req.body.rol === 'admin') await db.query('DELETE FROM registros');\n  res.sendStatus(200);\n});\napp.get('/api/buscar', async (req,res) => {\n  res.json(await db.query(\"SELECT * FROM personal WHERE nombre='\" + req.query.nombre + \"'\"));\n});\napp.get('/api/admin/exportar', (req,res) => {\n  exec('pg_dump gestion > ' + req.query.archivo, (err,out) => res.send(err ? err.message : out));\n});\napp.use((err,req,res,next) => res.status(500).send(err.stack));\napp.listen(3001);",
    "api/login.demo.js": "// Fragmento ficticio; PIN no válido fuera del ejemplo.\nconst ADMIN_PIN = '0000-DEMO-NO-VALIDO';\nif (req.body.pin === ADMIN_PIN) res.json({rol:'admin'});",
    "compose.demo.yaml": "# Documento ficticio\nservices:\n  db:\n    image: postgres:16\n    ports: ['5432:5432']\n    environment:\n      POSTGRES_USER: postgres\n      POSTGRES_DB: gestion\n    volumes: ['./datos:/var/lib/postgresql/data']\n    restart: 'no'",
    "web/vite.demo.ts": "// Configuración ficticia\nexport default {server: {host:'0.0.0.0', proxy:{'/api':'http://localhost:3001'}}};",
    "package.demo.json": '{"private":true,"scripts":{"dev":"vite --host"},"dependencies":{"react":"18.2.0","vite":"4.0.0","express":"4.18.2","pg":"8.11.0"}}',
    "operacion.demo.txt": "Escenario inventado.\nWeb y API arrancadas en terminales personales sin supervisor documentado.\nLa base conserva datos en ./datos del PC.\nNo hay mediciones aportadas de memoria, CPU, concurrencia ni volumen de datos.\nNo hay lockfile ni resultado real de un scanner en este ejemplo.",
}
snapshot = {
    "repository": "SIMULACIÓN · Portal de personal", "simulation": True,
    "branch": "ficticia", "commit": "SIN-COMMIT-REAL", "analyzed_at": datetime.now(timezone.utc).isoformat(),
    "evidence_origin": "SIMULACIÓN: contenido escrito a mano para revisar el formato. No se descargó ni analizó ningún repositorio. 0 llamadas a modelos; 0 tokens de agentes.",
    "files": [{"path": p, "text": t} for p, t in SOURCES.items()], "excluded": [],
    "bytes_read": sum(len(t.encode()) for t in SOURCES.values()),
}
snapshot.update(project_name="Portal de personal", source_revision="demo-ficticio-portal-personal",
                evidence_origin="EJEMPLO FICTICIO · adaptación editorial v12 del escenario escrito a mano. Sin repositorio real, agentes, scanners ni llamadas a modelos. El ejemplo anterior se conserva.")


def ref(path, line):
    return {"path": path, "line": line, "quote": SOURCES[path].splitlines()[line - 1]}


def finding(topic, severity, control, observation, impact, action, pending, conditions, refs, **extra):
    return dict(tema=topic, severidad=severity, control=control, observacion=observation,
                importancia=impact, accion=action, pendiente=pending, condiciones=conditions,
                evidencia=refs, **extra)


def fact(topic, observation, refs, **extra):
    return finding(topic, "informativa", "contexto", observation, "Contextualiza la aplicación y su operación.",
                   "Contrastar con la implementación real.", "No se ha revisado la iniciativa real.", "Solo describe el ejemplo inventado.", refs, **extra)


api = "api/server.demo.js"
security = {
    "schema_version": 3, "confirmados": [
        finding("acceso", "critica", "entradas", "El nombre de archivo recibido se concatena en un comando de shell para exportar la base de datos.",
                "Si la ruta es alcanzable, una entrada manipulada podría ejecutar comandos con la identidad del proceso y acceder a sus datos.",
                "Eliminar el shell; usar una API de exportación con argumentos separados y un destino controlado.", "Probar rechazo de entradas maliciosas y confirmar permisos del proceso.",
                "Patrón representado en el ejemplo; no se ejecutó ni se demostró explotación.", [ref(api, 15), ref(api, 16)]),
        finding("datos", "critica", "entradas", "El buscador construye SQL concatenando el nombre enviado por el solicitante.",
                "Una entrada manipulada podría alterar la consulta y ampliar la lectura de información de personal.",
                "Parametrizar la consulta y aplicar autorización sobre los registros devueltos.", "Verificar consultas, permisos de la cuenta de BD y casos de abuso.",
                "Depende de que el endpoint sea accesible y del alcance de los permisos efectivos de BD.", [ref(api, 12), ref(api, 13)]),
        finding("acceso", "alta", "acceso", "La operación de borrado decide el permiso a partir del rol enviado en el cuerpo de la solicitud.",
                "Un cliente podría declararse administrador y solicitar un borrado masivo.",
                "Resolver identidad y permisos en el servidor; exigir autorización para cada operación sensible.", "Validar sesiones, roles y rechazo de llamadas sin privilegios.",
                "En el escenario no se aplica un control anterior a la ruta; el efecto real no está probado.", [ref(api, 8), ref(api, 9)]),
        finding("datos", "alta", "acceso", "La ruta de listado devuelve todos los registros sin autenticación ni filtro por usuario en el servidor del ejemplo.",
                "Una persona que alcance la ruta podría obtener información de otros empleados.",
                "Autenticar peticiones y limitar filas y campos según la función y el usuario.", "Definir quién debe acceder a qué datos y probar accesos cruzados.",
                "No se da por demostrada exposición en Internet; depende del acceso permitido por red y túnel.", [ref(api, 2), ref(api, 4), ref(api, 6)]),
        finding("acceso", "alta", "secretos", "El acceso administrativo utiliza un PIN fijo escrito en el código del escenario.",
                "Si se utilizara una credencial compartida real, permitiría suplantaciones y dificultaría atribuir acciones.",
                "Sustituir el PIN compartido por identidad corporativa y autorización en el servidor.", "Revisar gestión de identidad y revocar credenciales reales si estuvieran expuestas.",
                "El valor incluido es ficticio e inválido; no se ha encontrado ningún secreto real.", [ref("api/login.demo.js", 2), ref("api/login.demo.js", 3)]),
        finding("estabilidad", "media", "operacion", "El listado recupera y devuelve todos los registros de personal en una sola petición.",
                "El tamaño de respuesta y el trabajo pueden crecer con el número de registros y afectar la disponibilidad.",
                "Añadir paginación, tamaño máximo de página y límites de petición.", "Medir volumen, concurrencia, tiempos y consumo antes de dimensionar.",
                "No existen mediciones; no se afirma que el sistema ya agote memoria ni CPU.", [ref(api, 5), ref(api, 6)]),
        finding("estabilidad", "baja", "operacion", "El manejador de errores devuelve la traza completa al cliente.",
                "Puede revelar rutas y detalles internos útiles para otras acciones.",
                "Devolver un error público estable y registrar el detalle en un destino restringido.", "Comprobar respuesta final y evitar datos personales en registros.",
                "La información revelada dependería del error que se produzca.", [ref(api, 18)]),
    ], "indicios": [
        finding("acceso", "alta", "configuracion", "El puerto PostgreSQL se publica en el host sin una dirección de enlace específica.",
                "Si la red y el firewall permiten alcanzarlo, la base podría ser accesible desde equipos no previstos.",
                "Retirar la publicación innecesaria y restringir conectividad al backend.", "Verificar interfaces, firewall, autenticación y acceso efectivo.",
                "Publicar el puerto no demuestra que sea accesible desde Internet.", [ref("compose.demo.yaml", 5)],
                por_confirmar="Desde qué redes puede alcanzarse el puerto y con qué controles."),
        finding("datos", "media", "configuracion", "La configuración declara una cuenta denominada postgres para la base.",
                "Si conserva permisos administrativos, comprometer la aplicación ampliaría el impacto sobre datos y esquema.",
                "Utilizar una cuenta de aplicación con permisos mínimos y separar migraciones.", "Inspeccionar permisos efectivos y configuración activa.",
                "El nombre de una cuenta por sí solo no demuestra sus privilegios reales.", [ref("compose.demo.yaml", 7)],
                por_confirmar="La cuenta efectiva y sus permisos, que no se han comprobado."),
    ], "dudas": ["¿Qué personas deben acceder y qué operaciones puede realizar cada rol?", "¿Qué datos de personal son necesarios y quién autoriza su tratamiento?"], "controles": []}
for key in CONTROLS:
    items = [x for x in security["confirmados"] + security["indicios"] if x["control"] == key]
    security["controles"].append({"id": key, "estado": "hallazgo" if items else "no_evaluado",
                                 "motivo": "Riesgos ficticios representados en este dominio; revisión real pendiente." if items else "No hay versiones resueltas ni comprobaciones reales de dependencias en este ejemplo.",
                                 "evidencia": items[0]["evidencia"][:2] if items else []})

architecture = {"schema_version": 3, "controles": [], "confirmados": [
    fact("arranque", "La web y la API se ejecutan en terminales del PC; PostgreSQL se inicia con Docker Compose y un túnel da acceso a la web.", [ref("README.demo.md", 4), ref("README.demo.md", 6)]),
    finding("estabilidad", "media", "operacion", "La operación del ejemplo depende de que el PC personal y sus procesos permanezcan encendidos.",
            "Apagar el equipo o cerrar los procesos interrumpe el acceso y las operaciones.",
            "Trasladar la ejecución a un servicio gestionado y configurar arranque, salud y registros.", "Comprobar reinicios y restauración en un entorno de prueba.",
            "Es una dependencia operativa del escenario, no una medición de incidentes reales.", [ref("README.demo.md", 5), ref("operacion.demo.txt", 2)]),
    fact("datos", "La base contiene datos personales y utiliza una carpeta del disco del PC para conservar sus archivos.", [ref("README.demo.md", 3), ref("compose.demo.yaml", 9)]),
], "indicios": [
    finding("recuperacion", "alta", "operacion", "No se aportan procedimientos de copia, restauración ni responsables de operación.",
            "Si no existen copias utilizables, un fallo del disco o borrado podría impedir recuperar la información.",
            "Identificar copias, acceso a ellas, responsable y prueba de restauración.", "Aportar evidencia de una restauración y acordar pérdida y tiempo de recuperación aceptables.",
            "Que no se documenten no prueba que no existan mecanismos externos.", [ref("README.demo.md", 7)], por_confirmar="Qué copias existen fuera del PC y si permiten restaurar los datos."),
], "dudas": ["¿El túnel exige identidad o permite acceso a cualquiera que conozca el enlace?", "¿Qué volumen de datos, usuarios concurrentes y horarios de uso deben soportarse?"],
"propuesta_azure": {
    "estado": "propuesta_preliminar", "destino": "app_service",
    "resumen": "Proponer una sola aplicación en App Service que sirva el frontend compilado y la API, con PostgreSQL gestionado. Sustituir el PC y el túnel; corregir primero los riesgos críticos del ejemplo.",
    "justificacion": "Es una aplicación web pequeña con API HTTP y un único motor relacional. Un servicio web y una base gestionada son un punto de partida sencillo; no se observa una necesidad de crear Kubernetes.",
    "evidencia": [ref("README.demo.md", 2), ref("compose.demo.yaml", 4), ref("web/vite.demo.ts", 2)],
    "supuestos": ["La web puede compilarse como estáticos y servirse junto a la API; habría que adaptar y probar el arranque.", "Hay una suscripción y un entorno corporativo autorizados; no se presupone red, identidad ni presupuesto.", "PostgreSQL gestionado es compatible con esquema, extensiones y datos; hay que verificarlo antes de migrar."],
    "servicios": [
        {"servicio": "Azure App Service", "uso": "Alojar un contenedor con web compilada y API; añadir identidad y autorización reales, sin exponer el modo de desarrollo."},
        {"servicio": "Azure Database for PostgreSQL Flexible Server", "uso": "Conservar el mismo motor, restringir el acceso al backend y configurar copias y restauración comprobada."},
        {"servicio": "Azure Container Registry", "uso": "Guardar imágenes versionadas; reutilizar el registro corporativo si está disponible."},
        {"servicio": "Azure Monitor / Application Insights", "uso": "Centralizar registros mínimos y una alerta de disponibilidad, revisando datos personales, retención y coste."},
    ],
    "pasos": ["Corregir inyección, autorización y PIN fijo; añadir Dockerfile de producción con frontend compilado y configuración externa. No existe en el escenario actual.",
              "Azure Pipelines: compilar, ejecutar pruebas disponibles y un smoke test propuesto, construir imagen y publicarla en ACR con versión identificable.",
              "Preparar entorno de prueba: identidad y permisos mínimos, secretos fuera de Git e imagen, base restringida, HTTPS y registros sin información sensible.",
              "Ensayar migración y restauración de PostgreSQL; validar permisos y recorridos críticos. El arquitecto aprueba antes de publicar para los usuarios.",
              "Desplegar la imagen aprobada y comprobar salud. Conservar la versión anterior para volver atrás; un cambio de esquema requiere su propio plan y copia verificada."],
    "pendientes": ["Confirmar política de identidad, acceso externo y tratamiento de datos de personal.", "Resolver críticos y altos; verificar que la conexión a la base no quede abierta a redes no autorizadas.", "Medir consumo y concurrencia para elegir capacidad; no se proponen SKU ni precios sin datos.", "Confirmar responsable operativo, compatibilidad de versiones y una restauración ensayada."],
}}

inventory = {"schema_version": 3, "controles": [], "confirmados": [
    fact("proposito", "Registrar asistencia, ausencias y tareas del personal junior desde una aplicación creada por el área de negocio.", [ref("README.demo.md", 2)]),
    fact("componentes", "Frontend React con Vite, API Node/Express y PostgreSQL en Docker; el acceso se realiza a través de un túnel hacia el PC.", [ref("package.demo.json", 1), ref("compose.demo.yaml", 4), ref("README.demo.md", 6)], componente={"nombre": "Portal web y API", "tecnologia": "React 18.2, Vite 4, Node/Express 4.18 y pg 8.11 (declaraciones ficticias)", "funcion": "Interfaz y operaciones HTTP de gestión de personal."}),
    fact("componentes", "PostgreSQL 16 conserva los datos en una carpeta local enlazada al contenedor.", [ref("compose.demo.yaml", 4), ref("compose.demo.yaml", 9)], componente={"nombre": "Base de datos", "tecnologia": "PostgreSQL 16 en Docker Compose", "funcion": "Persistencia de personal, horarios y registros."}),
    fact("datos", "Se registran nombres, correos corporativos, horarios y observaciones internas; no hay datos personales reales en este ejemplo.", [ref("README.demo.md", 3)]),
], "indicios": [], "dudas": ["¿Existen otros servicios, integraciones o archivos que no aparezcan en el escenario?", "¿Qué dependencias y versiones se utilizan realmente? La antigüedad de una versión no demuestra una vulnerabilidad."]}

# Editorial wording is authored for this fictional fixture only. The renderer never
# performs these replacements or applies these statements to another repository.
titles = [
    "Órdenes no autorizadas al servidor", "Lectura de datos fuera de lo permitido",
    "Borrado solicitado sin permiso de administrador", "Información de otras personas visible sin autorización",
    "Acceso administrativo con un PIN compartido", "Listados que podrían afectar al servicio", "Detalles internos visibles en errores",
]
plain = [
    ("La exportación utiliza un nombre de archivo enviado por el usuario para construir una orden del sistema.", "Un nombre manipulado podría permitir ejecutar otras órdenes y acceder a datos.", "Separar el nombre del archivo de las instrucciones de exportación y aceptar solo destinos permitidos.", "El nombre enviado no cambia las órdenes que ejecuta el servidor.", "El mecanismo técnico es concatenación de entrada no confiable en un comando de shell; puede permitir inyección de comandos."),
    ("El buscador incorpora directamente lo que escribe el usuario a la consulta de datos.", "Una búsqueda manipulada podría devolver información que no debería mostrarse.", "Separar los valores de búsqueda de las instrucciones de consulta y comprobar los permisos sobre los resultados.", "Un dato manipulado no cambia la consulta prevista ni amplía el acceso autorizado.", "Construcción de SQL mediante concatenación. Las consultas parametrizadas separan los valores de la instrucción SQL."),
    ("La operación de borrado acepta el rol de administrador que declara quien hace la solicitud.", "Una persona podría declararse administradora y solicitar un borrado indebido.", "Comprobar en el servidor la identidad de la persona y su permiso para borrar.", "Las solicitudes sin permiso no pueden borrar registros.", "La autorización se basa en req.body.rol, un dato controlado por el cliente; requiere verificación del permiso en servidor."),
    ("El listado del ejemplo devuelve información de todas las personas sin comprobar quién la solicita.", "Una persona con acceso a esa función podría ver información ajena.", "Usar cuentas individuales y limitar datos y operaciones a lo autorizado para cada cuenta.", "Cada persona ve solo la información que le corresponde.", "La ruta GET /api/personal carece de middleware de autenticación o filtrado de filas en el pseudocódigo completo mostrado."),
    ("Se utiliza un PIN fijo escrito en el código para obtener acceso administrativo. El valor es ficticio.", "Si fuera una credencial compartida real, varias personas podrían usar el mismo acceso sin identificar quién actuó.", "Sustituir el PIN por cuentas individuales y permisos administrados en el servidor.", "El PIN deja de dar acceso y cada acción puede asociarse a una cuenta autorizada.", "Credencial fija incorporada al código del ejemplo; no se ha detectado ninguna credencial real ni se ha probado su actividad."),
    ("El listado devuelve todos los registros en una sola respuesta, sin dividirlos en páginas.", "Al crecer los datos o las consultas simultáneas, las respuestas podrían tardar más y afectar a otros usuarios.", "Dividir el listado por páginas, limitar su tamaño y medir el funcionamiento con un volumen representativo.", "Las respuestas permanecen acotadas y la capacidad se elige con mediciones.", "Consulta sin paginación y materialización completa del resultado; no hay mediciones de CPU, RAM, tiempos ni concurrencia."),
    ("Cuando ocurre un error, el ejemplo devuelve al cliente información interna del fallo.", "Puede revelar rutas y detalles del servicio que faciliten otras acciones.", "Mostrar un mensaje público breve y guardar el detalle en registros con acceso restringido.", "Los usuarios reciben errores comprensibles sin detalles internos innecesarios.", "El manejador serializa err.stack en la respuesta HTTP. La información revelada depende de la excepción."),
]
for item, title, wording in zip(security["confirmados"], titles, plain):
    observation, impact, action, expected, technical = wording
    item.update(titulo=title, observacion=observation, importancia=impact, accion=action, resultado_esperado=expected, detalle_tecnico=technical)
for item, title in zip(security["indicios"], ("Acceso a la base desde equipos no previstos", "Permisos de la cuenta de base de datos por confirmar")):
    item.update(titulo=title, resultado_esperado="El acceso a la base y sus permisos quedan limitados a lo necesario; debe comprobarse.")
architecture["confirmados"][1].update(titulo="Interrupción del servicio al apagar el PC", resultado_esperado="El servicio puede arrancar y recuperarse sin depender de terminales personales; debe comprobarse.")
architecture["indicios"][0].update(titulo="Recuperación de datos sin acreditar", resultado_esperado="Existe una copia accesible fuera del PC y una restauración ensayada.")
architecture["presentacion"] = {
    "flujo_actual": {
        "componentes": [
            {"id": "tunel", "nombre": "Acceso remoto", "descripcion": "Túnel hacia el PC", "evidencia": [ref("README.demo.md", 6)]},
            {"id": "web", "nombre": "Web", "descripcion": "React / Vite", "evidencia": [ref("package.demo.json", 1), ref("web/vite.demo.ts", 2)]},
            {"id": "api", "nombre": "Servicio de aplicación", "descripcion": "Node / Express", "evidencia": [ref(api, 19), ref("package.demo.json", 1)]},
            {"id": "db", "nombre": "Datos", "descripcion": "PostgreSQL", "evidencia": [ref("compose.demo.yaml", 4)]},
        ],
        "conexiones": [
            {"origen": "tunel", "destino": "web", "estado": "observada", "descripcion": "El túnel apunta al servicio web del PC; falta verificar quién puede utilizarlo.", "evidencia": [ref("README.demo.md", 6)]},
            {"origen": "web", "destino": "api", "estado": "observada", "descripcion": "La web redirige las solicitudes de aplicación al servicio del PC.", "evidencia": [ref("web/vite.demo.ts", 2)]},
            {"origen": "api", "destino": "db", "estado": "inferida", "descripcion": "El código consulta una base y la configuración declara PostgreSQL; falta la configuración efectiva de conexión.", "evidencia": [ref(api, 5), ref("compose.demo.yaml", 4)]},
        ]},
    "estado_operativo": [
        {"aspecto": "motor", "estado": "observado", "descripcion": "PostgreSQL 16 declarado en Docker Compose.", "pendiente": "Comprobar la versión utilizada realmente.", "evidencia": [ref("compose.demo.yaml", 4)]},
        {"aspecto": "ubicacion", "estado": "observado", "descripcion": "Carpeta ./datos del disco del PC enlazada al contenedor.", "pendiente": "Identificar otros archivos o datos de negocio fuera de esa carpeta.", "evidencia": [ref("compose.demo.yaml", 9)]},
        {"aspecto": "acceso", "estado": "indicio", "descripcion": "El puerto de la base se publica a través del PC.", "pendiente": "Comprobar qué equipos pueden conectarse y qué controles de red se aplican.", "evidencia": [ref("compose.demo.yaml", 5)]},
        {"aspecto": "cuentas", "estado": "indicio", "descripcion": "La configuración declara la cuenta postgres; sus permisos no se han comprobado.", "pendiente": "Revisar la cuenta efectiva y sus permisos.", "evidencia": [ref("compose.demo.yaml", 7)]},
        {"aspecto": "copias", "estado": "no_evaluado", "descripcion": "No se aportan procedimientos ni resultados de copia.", "pendiente": "Localizar copias fuera del PC y confirmar su responsable.", "evidencia": []},
        {"aspecto": "recuperacion", "estado": "no_evaluado", "descripcion": "No se aportan pruebas de recuperación de datos.", "pendiente": "Ensayar una restauración y acordar pérdida de datos e interrupción aceptables.", "evidencia": []},
        {"aspecto": "disponibilidad", "estado": "observado", "descripcion": "Depende del PC y de programas abiertos manualmente.", "pendiente": "Comprobar arranque tras reinicios y fallos; no hay mediciones de disponibilidad.", "evidencia": [ref("README.demo.md", 5), ref("operacion.demo.txt", 2)]},
        {"aspecto": "capacidad", "estado": "no_evaluado", "descripcion": "Sin mediciones de uso ni consumo.", "pendiente": "Medir datos, usuarios simultáneos, tiempos de respuesta, procesador y memoria.", "evidencia": []},
    ],
    "decision": {"propuesta": "Encargar correcciones y un ensayo controlado", "evidencia_pendiente": ["Usuarios, permisos, reglas de acceso remoto y datos necesarios definidos.", "Restauración ensayada y responsable operativo identificado.", "Volumen, concurrencia y consumo medidos.", "Compatibilidad y pruebas en el entorno Azure autorizado."], "siguiente_paso": "Revisar las correcciones, completar la evidencia pendiente y decidir si procede el ensayo en Azure."},
}
inventory["presentacion"] = {"resumen": {"descripcion": "Aplicación de gestión de personal para registrar asistencia, ausencias y tareas.", "tecnologia_principal": "JavaScript", "evidencia": [ref("README.demo.md", 2), ref("package.demo.json", 1)]}}
for service, category in zip(architecture["propuesta_azure"]["servicios"], ("ejecucion", "datos", "entrega", "monitorizacion")):
    service["categoria"] = category
architecture["propuesta_azure"]["conexiones"] = [
    {"origen": 1, "destino": 2, "descripcion": "Acceso restringido de la aplicación a los datos; por diseñar y comprobar."},
    {"origen": 3, "destino": 1, "descripcion": "Entrega de una versión identificable tras pruebas y aprobación humana."},
    {"origen": 1, "destino": 4, "descripcion": "Registros y alertas propuestos, con acceso y conservación definidos."},
]

cells = []
results = []
for cell_id, name, result in (("security", "Seguridad", security), ("architecture", "Arquitectura y migración", architecture), ("inventory", "Inventario tecnológico", inventory)):
    valid = validate_report(json.dumps(result), snapshot, {"confirmados": 12, "indicios": 8, "dudas": 8})
    cells.append({"id": cell_id, "nombre": name, "estado": "simulada", "model": "Sin modelo", "reasoning": "no aplica", "archivos": list(SOURCES), "usage": {"api_calls": 0, "total_tokens": 0}})
    results.append((cell_id, valid))
data = consolidate(results, cells)
data.update(estado="simulacion", simulation=True, scanners=[
    {"name": "Gitleaks", "status": "no_evaluado", "findings": [], "detail": "No ejecutado: todos los archivos y hallazgos son ficticios."},
    {"name": "OSV-Scanner", "status": "no_evaluado", "findings": [], "detail": "No ejecutado: no se inventan avisos CVE ni resultados de herramientas."},
])
output = ROOT / "reports" / RUN_ID
output.mkdir(parents=True, exist_ok=True)
for name, value in (("evidencia.json", snapshot), ("informe.json", data), ("estado.json", {"estado": "simulacion", "celulas": cells}), ("job.json", {"id": RUN_ID, "repository": snapshot["repository"], "estado": "simulacion", "created": snapshot["analyzed_at"]})):
    (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
(output / "informe.md").write_text(markdown(data, snapshot, "SIN MODELO · FICTICIO"), encoding="utf-8")
(output / "informe.html").write_text(render_html(data, snapshot), encoding="utf-8")
print(str(output))
