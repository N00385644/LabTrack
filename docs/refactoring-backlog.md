# Backlog de Refactorización y Deuda Técnica — LabTrack

**Curso:** Calidad y Pruebas de Software · **Caso de Estudio T3:** Sistema de Gestión de Laboratorios "LabTrack"  
**Docente:** Mark Anthony Arribasplata Palomino  
**Versión evaluada:** 1.0.0 · **Fecha:** 09/11/2026  
**Insumo de entrada:** Auditoría de análisis estático con SonarQube Community Build 26.10.0.133078 y SonarScanner CLI 8.3.1.16491 sobre `backend/src` y `frontend/src`, complementada con el análisis de pruebas unitarias de Vitest y pruebas de carga/estrés con Apache JMeter 5.6.3.

---

## 1. Contexto del Proyecto y Naturaleza de las Evidencias

LabTrack es un sistema integral para la reserva y administración de equipos de laboratorio de cómputo, electrónica y redes en la Universidad Privada del Norte.

> [!IMPORTANT]
> **Aclaración sobre la línea base y reproducción:**
> El repositorio Git de LabTrack cuenta con un único commit histórico (`840052e`, «Initial commit»). Para auditar con rigor el proceso de refactorización y contrastar el estado previo frente al estado final en un servidor local real de SonarQube (localhost:9000), el código del **ANTES es REPRODUCIDO** en `docs/evidencias-sonarqube/antes/src/` reinyectando los 44 defectos documentados en `docs/sonar-baseline.json`. Los escaneos en SonarQube arrojaron 44 issues iniciales (1 bug, 2 vulnerabilidades y 41 code smells; confiabilidad B, seguridad C, mantenibilidad A) frente a 0 issues finales (0 bugs, 0 vulnerabilidades, 0 code smells; calificaciones A/A/A).

---

## 2. Criterios de Priorización de Deuda Técnica

Para clasificar los defectos técnicos y planificar su resolución, el equipo definió una escala de prioridades basada en el riesgo arquitectural, la seguridad de la información y la mantenibilidad del código:

| Prioridad | Criterio de Impacto | Regla de Compromiso |
|---|---|---|
| **Alta (P1)** | Vulnerabilidades de seguridad (CWE/OWASP), fallas directas de accesibilidad o confiabilidad (Bugs) y ternarios anidados que dificultan la trazabilidad del negocio. | **Bloqueante**: Debe corregirse y validarse al 100 % antes del pase a producción. |
| **Media (P2)** | Complejidad cognitiva elevada, inmutabilidad débil en contratos de interfaz (props sin Readonly), inconsistencias de nombrado en excepciones y omisiones de configuración en escáneres de calidad. | **Requerido**: Se resuelve dentro del ciclo actual de calidad y se verifica con la suite de pruebas. |
| **Baja (P3)** | Deuda técnica de bajo riesgo operativo, pruebas complementarias en navegadores adicionales o desacoplamiento de datos demo en entornos no productivos. | **Planificado / Aceptado**: Documentado con plan de mitigación para iteraciones posteriores. |

---

## 3. Matriz del Backlog de Refactorización

La siguiente tabla consolida los defectos identificados en el código inicial, su clasificación, módulos involucrados, la solución técnica adoptada y la evidencia verificable de cierre:

| ID | Defecto / Hallazgo | Prioridad | Archivos / Módulos | Solución | Estado | Evidencia de validación |
|---|---|---|---|---|---|---|
| **RF-01** | **Ternarios anidados múltiples (SonarQube `typescript:S3358`)**<br>Expresiones ternarias con más de 2 niveles de anidamiento que reducen la legibilidad y aumentan la probabilidad de errores lógicos. | **Alta** | `backend/src/admin/admin.service.ts`<br>`frontend/src/pages/AdminHistoryPage.tsx`<br>`frontend/src/pages/AdminPendingPage.tsx`<br>`frontend/src/pages/AdminReturnsPage.tsx`<br>`frontend/src/pages/CatalogPage.tsx`<br>`frontend/src/pages/MyReservationsPage.tsx` | Reemplazo de los operadores ternarios anidados por estructuras `if/else` explícitas en backend y bifurcaciones condicionales independientes en el JSX de React. | **Completado** | 8 incidencias de la regla S3358 eliminadas en SonarQube; pruebas de integración y de renderizado aprobadas. |
| **RF-02** | **Accesibilidad e interactividad no nativa en diálogos (SonarQube `typescript:S1082`, `S6819`, `S6847`)**<br>Elemento `div` con `role="dialog"` y overlay con manejador `onClick` sin soporte de teclado (Bug S1082) ni semántica nativa (S6819/S6847). | **Alta** | `frontend/src/components/ui.tsx` (Componente `Modal`) | Migración del modal al elemento nativo HTML5 `<dialog open>`, y conversión del fondo oscuro en un `<button type="button" aria-label="Cerrar modal">` accesible para lectores de pantalla y navegación por teclado (Enter/Espacio/Esc). | **Completado** | Bug S1082 resuelto; code smells S6819 y S6847 eliminados; calificación de Confiabilidad elevada a **A** (0 bugs) en SonarQube. |
| **RF-03** | **Generador de números pseudoaleatorios criptográficamente débil (SonarQube `typescript:S2245`)**<br>Uso de `Math.random()` para generar identificadores de notificaciones toast, vulnerable a colisiones y predictibilidad. | **Alta** | `frontend/src/contexts/ToastContext.tsx` | Reemplazo de `Math.random()` por un generador de secuencia monotónica local en memoria (`let toastSequence = 0; const id = ++toastSequence;`). | **Completado** | Vulnerabilidad S2245 cerrada en SonarQube (`despues/capturas-reales/03-seguridad.png`: 0 vulnerabilidades). |
| **RF-04** | **Credenciales de demostración embebidas en código fuente (SonarQube `typescript:S2068`)**<br>Contraseña en texto plano (`Estudiante2026!`) hardcodeada en el componente de login para los botones de acceso rápido. | **Alta** | `frontend/src/pages/LoginPage.tsx` | Externalización de contraseñas hacia variables de entorno de Vite (`import.meta.env.VITE_DEMO_STUDENT_PASSWORD` y `VITE_DEMO_ADMIN_PASSWORD`), ocultando los accesos rápidos si las variables no están definidas. | **Completado** | Vulnerabilidad S2068 eliminada; calificación de Seguridad elevada a **A** (0 vulnerabilidades) en SonarQube. |
| **RF-05** | **Propiedades de componentes sin marca de solo lectura (SonarQube `typescript:S6759`)**<br>Definición de props en componentes React sin envolver en `Readonly<T>`, permitiendo mutaciones accidentales del estado recibido. | **Media** | `frontend/src/components/ui.tsx`<br>`frontend/src/components/AppLayout.tsx`<br>`frontend/src/components/CategoryIconLabel.tsx`<br>`frontend/src/components/ProtectedRoute.tsx`<br>`frontend/src/contexts/AuthContext.tsx`<br>`frontend/src/contexts/ToastContext.tsx`<br>`frontend/src/pages/CatalogPage.tsx` | Adición sistemática del modificador TypeScript `Readonly<{ ... }>` en todas las declaraciones de propiedades de componentes funcionales. | **Completado** | 14 incidencias de la regla S6759 erradicadas en el escaneo final de SonarQube. |
| **RF-06** | **Parámetros de captura nombrados `caught` fuera de convención (SonarQube `typescript:S7718`)**<br>Uso repetido de bloques `catch (caught)` en lugar del identificador estándar esperado por las directrices de código limpio. | **Media** | `frontend/src/pages/AdminHistoryPage.tsx`<br>`frontend/src/pages/AdminPendingPage.tsx`<br>`frontend/src/pages/AdminReturnsPage.tsx`<br>`frontend/src/pages/CatalogPage.tsx`<br>`frontend/src/pages/LoginPage.tsx`<br>`frontend/src/pages/MyReservationsPage.tsx`<br>`frontend/src/pages/NewReservationPage.tsx` | Renombrado sistemático del parámetro del bloque catch a `error_` (`catch (error_)`), normalizando la captura y logueo de excepciones en todas las páginas. | **Completado** | 11 incidencias de la regla S7718 resueltas en el reporte final de SonarQube. |
| **RF-07** | **Uso de atributo `autoFocus` en formularios (SonarQube `typescript:S9379`)**<br>Atributo `autoFocus` en el campo de código de usuario del login, afectando la navegación asistida en dispositivos móviles y tecnología de accesibilidad. | **Media** | `frontend/src/pages/LoginPage.tsx` | Eliminación del atributo `autoFocus` para permitir que el foco se gestione de manera natural y predecible por el usuario o navegador. | **Completado** | Incidencia S9379 resuelta; verificación de navegación accesible en interfaz. |
| **RF-08** | **Complejidad cognitiva excesiva en vista de historial (SonarQube `typescript:S3776`)**<br>La función principal de renderizado y filtrado acumulaba una complejidad cognitiva de 19 puntos (el umbral máximo permitido por SonarQube es 15). | **Media** | `frontend/src/pages/AdminHistoryPage.tsx` | Descomposición de la renderización condicional, extracción de variables intermedias para los contadores y simplificación de las ramas de carga y estados vacíos. | **Completado** | Incidencia S3776 resuelta; complejidad cognitiva reducida a < 15; código más mantenible. |
| **RF-09** | **Defecto de configuración: Omisión de reporte de cobertura LCOV en escaneo SonarQube**<br>En el escaneo puntual local de demostración, SonarQube reportó `0.0 %` de cobertura debido a que no se inyectó la propiedad `-Dsonar.javascript.lcov.reportPaths`. | **Media** | `sonar-project.properties`<br>Scripts de automatización CI/CD | Inclusión explícita de los reportes LCOV de Vitest (`backend/coverage/lcov.info` y `frontend/coverage/lcov.info`) en la configuración del scanner. Cobertura real verificada en Vitest: Backend 95.71 %, Frontend 90.26 %. | **Completado** | Reportes de cobertura V8/Istanbul archivados en `docs/evidencias-pruebas/unitarias/cobertura/` y reporte HTML validado. |
| **RF-10** | **Casos límite de reservas y ventanas horarias sin pruebas unitarias específicas**<br>Falta de cobertura automatizada para reservas contiguas (ej. 08:00–10:00 y 10:00–12:00), duración cero y límites de horario de atención (07:00 a 22:00). | **Media** | `backend/test/reservation-boundaries.extra.spec.ts`<br>`frontend/src/test/reservation-boundaries.extra.test.ts` | Creación de suites de prueba complementarias que verifican los límites horarios y documentan defectos simulados mediante `it.fails` contra mocks defectuosos locales. | **Completado** | Incremento de pruebas unitarias de 93 a 101 aprobadas (53 en backend y 48 en frontend; salida limpia con código 0). |
| **RF-11** | **Credenciales de demostración en datos sembrados (Seed de desarrollo)**<br>Existencia de usuarios con contraseñas conocidas en `prisma/seed.ts` para pruebas académicas. | **Baja** | `backend/prisma/seed.ts` | Aislamiento del seed para entornos de prueba (`labtrack_test`) y demostración; prohibición de ejecución del script en producción; documentación de advertencia en README. | **Aceptado** | Riesgo conocido y controlado para fines de evaluación académica en entorno local. |
| **RF-12** | **Pruebas de extremo a extremo automatizadas en navegadores adicionales (Cross-browser)**<br>La suite Selenium actual está validada sobre Google Chrome headless. | **Baja** | `frontend/e2e/` | Parametrizar la configuración de Selenium WebDriver para permitir la ejecución desatendida en Mozilla Firefox y Microsoft Edge en el pipeline de CI/CD. | **Planificado** | Agendado para la siguiente versión evolutiva (Sprint 2.0). |

---

## 4. Convención de Cierre y Verificación Técnica

Un defecto se clasifica como **Completado** únicamente tras cumplir simultáneamente tres condiciones objetivas:
1. **Integración limpia del código:** El cambio refactorizado está presente en los archivos fuente sin generar errores de tipado en TypeScript (`tsc --noEmit`).
2. **Suite de pruebas 100 % en verde:** La totalidad de las 101 pruebas unitarias (53 de backend y 48 de frontend) se ejecutan con éxito (`npm test`), confirmando que no existen regresiones funcionales ni cambios no deseados en la lógica de negocio.
3. **Validación en SonarQube:** El analizador estático confirma la desaparición total del hallazgo en el escaneo posterior, elevando las calificaciones de calidad del proyecto a **A / A / A** (0 bugs, 0 vulnerabilidades y 0 code smells).
