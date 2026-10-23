# Ejemplo ficticio del reporte

`create_fictional_report.py` construye un escenario escrito a mano de un portal de personal con problemas de seguridad y operación, y una propuesta DevOps Azure sencilla. No describe la iniciativa real ni sus resultados.

No consulta GitHub, no ejecuta agentes, no utiliza scanners ni llama a modelos. No genera consumo de tokens de los agentes. Los fragmentos son datos ficticios para representar evidencias, no una aplicación ejecutable.

Desde la raíz, con la imagen del auditor reconstruida para disponer del paquete instalado:

```powershell
docker run --rm --network none --volume "${PWD}:/workspace" --entrypoint python arktic-hermes-auditor:0.2.0 /workspace/examples/create_fictional_report.py
```

Abre en la oficina la revisión **SIMULACIÓN · Portal de personal** con identificador `demo-editorial-v12-portal-personal`, o el archivo `reports/demo-editorial-v12-portal-personal/informe.html`. El ejemplo anterior en `reports/demo-ficticio-portal-personal/` se conserva. Los informes generados se excluyen de Git; el ejemplo se reproduce con este script.

El ejemplo añade redacción y datos estructurados escritos a mano para mostrar el [estándar compartido](../docs/ESTANDAR_COMUNICACION_INFORMES.md). Ningún texto específico del escenario se utiliza como valor por defecto en el renderizador. La referencia `artifacts/propuesta-informe-direccion-arktic-v12.html` y sus versiones anteriores no se editan.

Las fuentes se identifican como ficticias, sin enlaces a repositorios reales. Las consultas a agentes están bloqueadas en esta simulación. Sirve para revisar presentación y utilidad; no valida la capacidad de detección del sistema ni una arquitectura real.
# Ejemplo de información insuficiente

`create_insufficient_example.py` crea `demo-informacion-insuficiente` con respuestas controladas y cero llamadas al modelo. Comprueba el estado terminal normal y un reporte breve sin apartados vacíos. No consulta GitHub ni ejecuta scanners y no reemplaza un ejemplo existente. Puede ejecutarse con el Python del auditor montando este repositorio en `/workspace` y lanzando `/workspace/examples/create_insufficient_example.py`.
