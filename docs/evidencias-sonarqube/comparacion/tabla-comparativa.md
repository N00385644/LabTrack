# Tabla comparativa SonarQube — ANTES vs DESPUÉS

> Datos reconstruidos desde `docs/sonar-baseline.json` y `docs/sonar-data.json`.
> **No es un escaneo nuevo**: SonarQube no estaba disponible el 2026-11-09.
> El estado ANTES se identifica como **ANTES REPRODUCIDO**.

Commit: `840052e769ac7386f458d9cac2332d6a4dd2d50d` · Fecha de captura: 2026-11-09

## Métricas principales

| Métrica | Antes | Después | Mejora |
|---|---:|---:|---|
| Bugs | 2 | 0 | -2 (-100 %) |
| Vulnerabilidades | 2 | 0 | -2 (-100 %) |
| Code Smells | 40 | 0 | -40 (-100 %) |
| Confiabilidad | B | A | B → A |
| Seguridad | C | A | C → A |
| Mantenibilidad | A | A | A → A (sin deuda abierta) |
| Quality Gate | OK | OK | OK → OK (0 issues abiertos) |

## Métricas secundarias

| Métrica | Antes | Después | Variación |
|---|---:|---:|---|
| Líneas de código (ncloc) | 4101 | 4120 | +19 |
| Cobertura | 89.6 % | 89.6 % | sin cambio |
| Duplicación | 0.7 % | 0.7 % | sin cambio |
| Complejidad ciclomática | 514 | 538 | +24 |
| Complejidad cognitiva | 303 | 297 | -6 |
| Issues abiertos | 44 | 0 | -44 (-100 %) |

## Lectura

- Los 44 hallazgos del ANTES (2 bugs, 2 vulnerabilidades, 40 code smells) se reducen a 0.
- Los ratings pasan de B/C/A a A/A/A.
- El quality gate permanece OK en ambas instantáneas; la diferencia es el número de issues abiertos.
- El ANTES no existe en Git: fue reconstruido en `docs/evidencias-sonarqube/antes/src`.
