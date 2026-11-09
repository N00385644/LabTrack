# Backlog de refactorización — LabTrack

**Curso:** Calidad y Pruebas de Software · **Versión:** 1.0.0 · **Fecha:** 09/11/2026  
**Insumo:** análisis estático con SonarQube Community Build 26.10 y SonarScanner CLI 8.3.1 sobre `backend/src` y `frontend/src`.

## Priorización

| Nivel | Criterio |
|---|---|
| **Alta** | Afecta reglas de negocio, seguridad o mantenibilidad de módulos centrales; se corrige antes del cierre. |
| **Media** | Deuda localizada que incrementa el costo de cambio o reduce la legibilidad; se corrige en el ciclo actual. |
| **Baja** | Mejora deseable sin impacto funcional inmediato; se planifica para el siguiente ciclo. |

## Backlog

| ID | Hallazgo / oportunidad | Severidad | Acción ejecutada o planificada | Estado | Evidencia |
|---|---|---|---|---|---|
| RF-01 | Ternarios anidados en `admin.service.ts` y en las páginas de administración, catálogo y reservas (S3358). | Alta | Reemplazar por bloques `if/else` y condiciones independientes en JSX. | Completado | 8 hallazgos S3358 eliminados; suites de API y UI en verde. |
| RF-02 | Modal con `role="dialog"` sobre un `div` y overlay con clic no accesible (S1082, S6819, S6847, S6848). | Alta | Migrar a `<dialog>` nativo y convertir el overlay en un botón con etiqueta accesible. | Completado | Pruebas de `AdminPendingPage` y `AdminReturnsPage`; navegación por teclado. |
| RF-03 | Identificadores de notificaciones generados con `Math.random()` (S2245). | Alta | Sustituir por un contador monotónico de módulo. | Completado | Vulnerabilidad S2245 cerrada. |
| RF-04 | Contraseñas de demostración embebidas en `LoginPage.tsx` (S2068). | Alta | Externalizar a variables `VITE_DEMO_*` y ocultar los accesos rápidos si no están configuradas. | Completado | Vulnerabilidad S2068 cerrada; `.env.example` documentado. |
| RF-05 | Props de componentes sin marcar como solo lectura (S6759), parámetros de captura con nombre no convencional (S7718) y `autoFocus` en el login (S9379). | Media | Aplicar `Readonly<...>`, renombrar `caught` a `error_` y retirar `autoFocus`. | Completado | 26 hallazgos menores eliminados. |
| RF-06 | Cobertura de ramas del frontend inferior a la del backend. | Media | Añadir pruebas de rutas, contextos, `AppLayout`, `ProtectedRoute`, historial y componentes compartidos. | Completado | 44 pruebas UI; cobertura de sentencias 90.5 %. |
| RF-07 | Credenciales de demostración en `prisma/seed.ts`. | Baja | Documentar como dato exclusivamente no productivo y externalizar en el pipeline. | Aceptado | Nota en README y en el informe. |
| RF-08 | Ramas defensivas de `AuthContext` (token expirado, refresco fallido) sin cobertura. | Baja | Añadir pruebas con token inválido y error de red. | Planificado | — |
| RF-09 | Ausencia de pruebas de accesibilidad automatizadas. | Baja | Integrar `axe-core` en la suite de React Testing Library. | Planificado | — |
| RF-10 | Pruebas E2E solo en Chrome. | Baja | Parametrizar Selenium para Firefox y Edge en CI. | Planificado | — |

## Convención de cierre

Un ítem se marca **Completado** solo si: (1) el cambio está integrado, (2) la suite completa sigue en verde y (3) el hallazgo desaparece o reduce su severidad en el siguiente escaneo de SonarQube. Los ítems **Aceptado** corresponden a riesgos conscientes documentados; los **Planificado** tienen responsable y ciclo asignado.
