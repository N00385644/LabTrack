# Pendientes del equipo — Informe LabTrack

**Curso:** Calidad y Pruebas de Software · **Caso T3:** Sistema de Gestión de Laboratorios "LabTrack"
**Fecha de esta revisión:** 09/11/2026

Este documento concentra todo lo que el informe **no puede afirmar por falta de información verificable**.
El informe usa marcadores visibles `[COMPLETAR POR EL EQUIPO: ...]` en lugar de inventar datos. Cuando el
equipo complete un marcador, debe reemplazarlo en `docs/generate_report.py`, regenerar el DOCX/PDF y volver
a revisar que el índice y la paginación sigan correctos.

---

## 1. Marcadores visibles en el informe (7)

| # | Marcador | Dónde aparece | Qué debe entregar el equipo |
|---|---|---|---|
| 1 | Antecedentes de investigación del proyecto, con autor, año, objetivo, metodología y resultado verificable; citar solo fuentes efectivamente leídas y enlazadas en las referencias. | Sección **Análisis del problema → Antecedentes** | 2–4 investigaciones reales (tesis o artículos) leídas por el equipo, con la cita APA 7 completa y una frase de qué aporta al proyecto. No citar trabajos que no se hayan leído. |
| 2 | Descripción formal de la organización (reseña institucional, población de usuarios, cantidad de laboratorios y equipos, procesos internos de préstamo y responsables), usando únicamente información oficial o proporcionada por la institución. | Sección **Análisis del problema → Descripción de la organización** | Datos oficiales de la UPN o de la coordinación de laboratorios: número de laboratorios, equipos, usuarios y flujo real de préstamo. Si no hay dato oficial, dejar el texto acotado al alcance del prototipo y **no** estimar cifras. |
| 3 | Marco de trabajo y cronograma efectivamente utilizados (sprints, iteraciones o fases), con fechas y responsables; si se usó Scrum u otro marco, adjuntar la evidencia de su aplicación. | Sección **Metodología de desarrollo** | Tabla de fases o sprints con fechas reales, responsables y entregables. Si el trabajo no siguió un marco formal, decirlo así y describir el ciclo realmente usado. |
| 4 | Características del hardware de las pruebas de rendimiento (CPU, memoria, disco, sistema operativo y versión de Chrome) para permitir la reproducción exacta. | Sección **Pruebas de carga y estrés con Apache JMeter** | Ficha de la máquina donde corrieron JMeter y Chrome: CPU, RAM, disco, SO y versión de navegador. Se puede obtener con `systeminfo` y `chrome://version`. |
| 5 | Diagrama de clases UML con servicios, controladores, DTO y entidades del dominio, generado a partir de `backend/src` y `frontend/src`. | Sección **Generación de soluciones → Diagrama de clases** | Diagrama UML real (PlantUML, draw.io o similar) exportado como imagen, más el archivo fuente. El informe ya describe los módulos y modelos; falta el gráfico formal. |
| 6 | Diagrama entidad-relación exportado desde Prisma o desde una herramienta de modelado, con cardinalidades y claves. | Sección **Generación de soluciones → Modelo y diagrama de base de datos** | Imagen del diagrama ER (por ejemplo `prisma ERD` o dbdiagram.io) con las cuatro entidades y sus relaciones. La tabla de modelos ya está verificada contra `schema.prisma`. |
| 7 | Diagrama de paquetes formal con dependencias permitidas y prohibidas entre módulos, si el curso exige el artefacto en notación UML. | Sección **Generación de soluciones → Diagrama de paquetes y modelo arquitectónico** | Diagrama de paquetes UML con las dependencias reales entre `auth`, `equipment`, `reservations`, `admin`, `prisma` y el frontend. La figura de arquitectura por capas ya existe, pero no es un diagrama de paquetes formal. |

---

## 2. Observaciones que impiden declarar conformidad total

No son marcadores del informe, pero deben quedar claras en la sustentación:

1. **Accesibilidad (D-02 / RF-14).** axe-core reporta una violación `color-contrast` en el inicio de sesión y
   17 nodos afectados en el catálogo. Está pendiente corregir la paleta y repetir la revisión hasta obtener
   cero violaciones. **WAVE no se ejecutó** y no se declara conformidad WCAG 2.1 AA.
2. **Historias sin evidencia verificable (7 de 12).** HU-06, HU-07, HU-08, HU-11, HU-13, HU-14 y HU-15
   están declaradas por el equipo pero no tienen código y pruebas verificables en el repositorio. El informe
   las presenta como brechas, no como funcionalidades implementadas.
3. **Testomat.io / TestLink no ejecutados.** Solo se entregan la plantilla y el CSV de interoperabilidad
   (`docs/evidencias-pruebas/testomatio-import.csv`). No se deben presentar capturas ficticias de estas
   herramientas; si el curso exige evidencia, hay que importar el CSV y capturar el reporte real.
4. **Cobertura en SonarQube = 0.0 %.** Es un defecto de configuración del escaneo (falta el reporte LCOV),
   no una medida real. La cobertura verificada con Vitest es 95.71 % en backend y 90.26 % en frontend.
5. **Porcentaje de participación en la portada.** La plantilla institucional deja `(% participación)` como
   texto abierto. El equipo debe reemplazarlo por el porcentaje acordado en cada nombre, tanto en el informe
   como en la presentación.
6. **Regresión E2E (D-01 / RF-13).** Está resuelta y documentada; no requiere acción, pero conviene
   recordarla en la defensa: la refactorización S6819 rompió los selectores de prueba, no el sistema.

---

## 3. Reglas para completar sin inventar

- Si un dato no se puede verificar, se deja el marcador o se acota el alcance con una frase explícita.
- No se agregan autores, años, porcentajes, antecedentes ni métricas que no estén respaldados por una fuente
  o por una ejecución real.
- Toda cifra del informe debe poder rastrearse a `docs/evidencias-*`, a `package.json` o a una ejecución
  reproducida en este repositorio.
- Después de completar un marcador, regenerar con `python docs/generate_report.py` y revisar el PDF completo.

---

## 4. Verificación rápida antes de entregar

```powershell
python docs/make_figures.py            # solo si se cambiaron los gráficos base
python docs/generate_report.py         # DOCX + PDF del informe
python docs/generate_presentation.py   # PPTX + PDF de la presentación
```

Comprobaciones mínimas:

- El PDF del informe abre y tiene portada, índices y anexos con numeración real.
- La presentación tiene exactamente 5 diapositivas.
- No quedan marcadores sin explicar ni cifras sin evidencia.
