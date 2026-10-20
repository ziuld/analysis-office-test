# Proyectos originales

Arktic Office reutiliza los siguientes proyectos. Las copias de sus avisos MIT corresponden a los commits fijados y deben conservarse junto con las fuentes y las distribuciones correspondientes.

| Proyecto | Fuente y versión | Aviso conservado |
|---|---|---|
| Hermes3D | [iamlukethedev/Hermes3D](https://github.com/iamlukethedev/Hermes3D), `beb76292747b816ef317aa6f9a3992e0014f81d9` | [MIT — Luke The Dev](licenses/Hermes3D-MIT.txt) |
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), `ce28ca328d3b85ac8663e602136eb69b027cd056` | [MIT — Nous Research](licenses/HermesAgent-MIT.txt) |

La adaptación de Hermes3D se distribuye como `docker/hermes3d-local-demo.patch`. El runtime de Hermes Agent se recupera sin un parche propio. Al preparar `vendor/`, los archivos `LICENSE` de ambos originales se mantienen en sus carpetas.

Las dependencias transitivas conservan sus propios avisos y licencias en los proyectos y paquetes correspondientes. Este archivo es una atribución de los dos proyectos base, no un inventario completo de dependencias ni una licencia del código propio de Arktic Office.
