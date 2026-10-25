# Proyectos originales

Arktic Office reutiliza los siguientes proyectos. Las copias de sus avisos MIT corresponden a los commits fijados y deben conservarse junto con las fuentes y las distribuciones correspondientes.

| Proyecto | Fuente y versión | Aviso conservado |
|---|---|---|
| Hermes3D | [iamlukethedev/Hermes3D](https://github.com/iamlukethedev/Hermes3D), `beb76292747b816ef317aa6f9a3992e0014f81d9` | [MIT — Luke The Dev](licenses/Hermes3D-MIT.txt) |
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), `ce28ca328d3b85ac8663e602136eb69b027cd056` | [MIT — Nous Research](licenses/HermesAgent-MIT.txt) |

La adaptación de Hermes3D se distribuye como `docker/hermes3d-local-demo.patch`. El runtime de Hermes Agent se recupera sin un parche propio. Al preparar `vendor/`, los archivos `LICENSE` de ambos originales se mantienen en sus carpetas.

Las dependencias transitivas conservan sus propios avisos y licencias en los proyectos y paquetes correspondientes. Este archivo es una atribución de los dos proyectos base, no un inventario completo de dependencias ni una licencia del código propio de Arktic Office.

La imagen del auditor también incluye [Gitleaks 8.30.1](https://github.com/gitleaks/gitleaks/tree/v8.30.1), con aviso [MIT](licenses/Gitleaks-MIT.txt), y [OSV-Scanner 2.7.0](https://github.com/google/osv-scanner/tree/v2.7.0), con licencia [Apache 2.0](licenses/OSV-Scanner-Apache-2.0.txt). Los avisos se copian a `/usr/local/share/licenses/arktic/` en la imagen. Versiones y hashes de los binarios Linux/amd64 están en `docker/install_scanners.py`.

El preparador experimental del Bloque 2 usa [Graphify 0.9.95](https://github.com/Graphify-Labs/graphify/tree/92741d162b2094ffc2fed58cfbd8ee823e9da62c), commit `92741d162b2094ffc2fed58cfbd8ee823e9da62c`, en una imagen independiente. Conserva [Apache-2.0](licenses/Graphify-LICENSE.txt), el [aviso MIT anterior](licenses/Graphify-LICENSE-MIT.txt) y [NOTICE](licenses/Graphify-NOTICE.txt); también se incluyen en `/usr/local/share/licenses/graphify/` en esa imagen. Las dependencias base se instalan desde su lockfile con el overlay PyYAML documentado en [Validación del indexador](docs/INDEXADOR.md). No se incorpora su integración de agentes/skills ni se instalan componentes en el host.


La imagen del auditor incluye además Semgrep Community Edition 1.182.1, sin modificaciones, en `/opt/semgrep`, separado del entorno Hermes. Conserva [LGPL-2.1-or-later](licenses/Semgrep-LGPL-2.1.txt) tomada del [paquete fuente exacto](https://pypi.org/project/semgrep/1.182.1/#files); el código fuente correspondiente se distribuye allí como `semgrep-1.182.1.tar.gz`. Los avisos se copian también a `/usr/local/share/licenses/arktic/`. Versión y hashes de instalación, incluidas sus dependencias propias, en `docker/semgrep-requirements.txt`. Las reglas locales de Arktic se mantienen en `semgrep-rules.json`; no se incorporan reglas de un registro externo ni componentes Pro.
