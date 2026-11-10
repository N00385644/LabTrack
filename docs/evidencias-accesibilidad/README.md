# Accesibilidad e inclusión (axe-core, equivalente a la extensión AXE)

**Contexto:** la plantilla del informe pide evaluar accesibilidad para usuarios con habilidades especiales (WAVE o AXE).
Se ejecutó axe-core 4.10.2 con las reglas WCAG 2.0/2.1 niveles A y AA sobre la pantalla de login y el catálogo del estudiante.

| Página | Reglas aprobadas | Violaciones | Detalle |
|---|---|---|---|
| Login | 19 | 1 (serious) | `color-contrast`: 1 elemento |
| Catálogo | 17 | 1 regla (serious) | `color-contrast`: 17 elementos |

**Lectura:** no hay fallas estructurales (etiquetas, roles, nombres accesibles, teclado); el único tipo de hallazgo es el
**contraste insuficiente de color** en textos secundarios. Está registrado en el backlog como defecto pendiente de corregir
(ajustar la paleta de grises/etiquetas a una razón de contraste >= 4.5:1). Los resultados completos están en `axe-resultados.json`.
No se ejecutó la extensión WAVE; solo axe-core.
