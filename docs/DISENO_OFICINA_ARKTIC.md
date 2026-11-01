# Estilo de la oficina ARKTIC

Rama de diseño: `codex/arktic-office-design`, creada desde `origin/main` después del merge del PR #7. El commit `94c35cc` conserva los últimos ajustes de interacción y controles antes de aplicar este estilo.

## Dirección visual

Interpretación pixel de las fotografías facilitadas: moqueta azul en puestos y reuniones, circulación azul verdosa, madera clara, paredes blancas cálidas y sillas blancas/grises. Cocina con suelo de madera y comedor. Identidad ARKTIC en listones de madera con letras claras, halo ámbar estático y punto turquesa.

| Material | Color base |
| --- | --- |
| Moqueta azul | `#384e67` |
| Circulación | `#799eaa` |
| Roble claro | `#d8c3a2` |
| Muebles blancos | `#f4f4ef` |
| Acento turquesa | `#42bcc6` |

Los colores son aproximaciones visuales, no una especificación corporativa medida.

## Cambios

- Estilo aplicado solo al mapa compacto de ARKTIC; el catálogo original conserva sus paletas y gráficos.
- Se mantienen 28 × 22 casillas, ocho puestos de trabajo, cuatro asientos de reunión y los accesos existentes.
- Escritorios de trabajo en madera clara con detalles blancos, sillas claras, ventanas con persianas grises y muros más luminosos.
- Panel pixel ARKTIC y tramo corto de listones sobre la partición existente.
- Comedor blanco con dos mesas iguales juntas y cuatro asientos funcionales (dos por lado), máquina expendedora verde y armario bajo de madera.
- Sofá gris azulado recolocado fuera de la cocina, con mesita auxiliar; sus destinos de asiento siguen al mueble.
- Sin cambios en llamadas a modelos ni estados de trabajo; continúan pausas, conversaciones ambientales y reservas.

## Verificación

42 pruebas de arte, mapa, ocupación, reuniones y conversaciones pasan. Se comprueba que los cuatro comensales lleguen a destinos distintos, que cada destino siga conectado, que los gráficos cubran sus paletas y tamaños y que el catálogo original no se modifique. ESLint de los archivos modificados sin errores ni avisos. Capturas de estilo en `artifacts/office-style-2026-11-01/` y del comedor de cuatro plazas en `artifacts/office-dining-2026-11-01/`.

Build de producción y TypeScript correctos. Oficina local actualizada y saludable; comprobados reposo, reuniones, móvil, ajuste del lienzo al abrir el panel y movimiento reducido. Cero errores de página y cero peticiones POST durante la comprobación visual, con datos interceptados solo en navegador y sin llamadas a modelos.

## Ajuste del comedor

Rótulo acortado a «Comedor» y elevado diez píxeles del mundo. Sillas orientadas hacia la mesa: variante frontal y respaldo por detrás del personaje para quienes miran hacia la cámara; la vista de espaldas conserva el respaldo delante. El orden de dibujo se aplica también a las sillas de reunión. Vista aislada de prueba con la escena real y los cuatro puestos ocupados para verificar orientación y profundidad, sin añadir controles de prueba al producto.

Las conversaciones sentadas mantienen la orientación del cuerpo hacia la mesa. Prueba de navegador con cuatro comensales y señales de conversación: fotograma sentado y orden personaje/silla comprobados en los cuatro puestos, además de revisión visual y tamaño del lienzo en móvil. Sin errores de página ni llamadas a modelos. La simulación larga de ocupación mantiene sus comprobaciones y dispone de 15 segundos de margen para entornos con carga.
