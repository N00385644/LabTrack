# Comparación REAL ANTES vs DESPUÉS (escaneos ejecutados en SonarQube local)

> Fuente: API de SonarQube `http://localhost:9000`, proyectos `labtrack-antes` y `labtrack-despues`,
> analizados con `sonar-scanner` 8.3.1 y el perfil **Sonar way comprehensive** (mismo perfil en ambos).
> El ANTES es **código REPRODUCIDO** (ver `../../antes/README-reproduccion.md`), no una versión histórica recuperada.

## Tabla comparativa

| Métrica | Antes | Después | Mejora |
|---|---|---|---|
| Bugs (clasificación clásica) | 1 | 0 | -1 |
| Vulnerabilidades | 2 | 0 | -2 |
| Code smells | 31 | 0 | -31 |
| Confiabilidad | B | A | B -> A |
| Seguridad | C | A | C -> A |
| Mantenibilidad | A | A | igual |
| Quality Gate | OK | OK | igual |
| Líneas de código (ncloc) | 4145 | 4120 | -25 |

## Hallazgos del ANTES por regla

| Regla | Clasificación | Cantidad | Archivos |
|---|---|---|---|
| `typescript:S7718` | CODE_SMELL | 11 | frontend/src/pages/AdminHistoryPage.tsx, frontend/src/pages/AdminPendingPage.tsx, frontend/src/pages/AdminReturnsPage.tsx, frontend/src/pages/CatalogPage.tsx, frontend/src/pages/LoginPage.tsx, frontend/src/pages/MyReservationsPage.tsx, frontend/src/pages/NewReservationPage.tsx |
| `typescript:S3358` | CODE_SMELL | 8 | backend/src/admin/admin.service.ts, frontend/src/pages/AdminHistoryPage.tsx, frontend/src/pages/AdminPendingPage.tsx, frontend/src/pages/AdminReturnsPage.tsx, frontend/src/pages/CatalogPage.tsx, frontend/src/pages/MyReservationsPage.tsx |
| `typescript:S6819` | CODE_SMELL | 5 | frontend/src/components/ui.tsx, frontend/src/contexts/ToastContext.tsx, frontend/src/pages/CatalogPage.tsx, frontend/src/pages/MyReservationsPage.tsx |
| `typescript:S7503` | CODE_SMELL | 3 | backend/src/audit/audit.service.ts, backend/src/equipment/equipment.service.ts |
| `typescript:S7785` | CODE_SMELL | 1 | backend/src/main.ts |
| `typescript:S1082` | BUG | 1 | frontend/src/components/ui.tsx |
| `typescript:S6847` | CODE_SMELL | 1 | frontend/src/components/ui.tsx |
| `typescript:S2245` | VULNERABILITY | 1 | frontend/src/contexts/ToastContext.tsx |
| `typescript:S3776` | CODE_SMELL | 1 | frontend/src/pages/AdminHistoryPage.tsx |
| `typescript:S2068` | VULNERABILITY | 1 | frontend/src/pages/LoginPage.tsx |
| `typescript:S9379` | CODE_SMELL | 1 | frontend/src/pages/LoginPage.tsx |
| `typescript:S6606` | CODE_SMELL | 1 | frontend/src/test/utils.tsx |

Total de issues ANTES: 35 (registro de la API). Total DESPUÉS: 0.

## Por qué no coincide exactamente con la línea base histórica (2 bugs / 2 vulnerabilidades / 40 smells)

* El escaneo histórico se hizo con otra versión de SonarQube y de su analizador; las reglas y su clasificación cambian entre versiones.
* La regla `S6759` (props sin `Readonly`, 14 casos en la línea base) **no fue reportada** por este escaneo real, y la versión nueva marca reglas distintas.
* Esta versión de SonarQube usa el modelo MQR (calidad de software: Seguridad / Confiabilidad / Mantenibilidad). La interfaz
  muestra 2 / 6 / 32 issues por calidad, porque un mismo issue puede afectar varias calidades; la API clásica cuenta
  1 bug, 2 vulnerabilidades y 31 code smells.
* Los valores históricos siguen documentados en `docs/sonar-baseline.json`; no se reemplazan ni se alteran.

## Quality Gate

Ambos proyectos: **OK** (Passed). El Quality Gate por defecto evalúa solo código nuevo, y en un primer
análisis no hay código nuevo comparable, por eso aprueba aunque el ANTES tenga hallazgos en el código total.
