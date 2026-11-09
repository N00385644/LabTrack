# Resumen de pruebas unitarias

## Contexto

La ejecución cubre las pruebas Vitest existentes de LabTrack y los casos límite agregados en archivos nuevos. Backend usa NestJS, Supertest y Prisma; frontend usa React Testing Library y jsdom.

## Resultados

| Suite | Archivos | Pruebas | Aprobadas | Fallidas | Cobertura |
|---|---:|---:|---:|---:|---|
| Backend `npm run test:cov` | 5 | 53 | 53 | 0 | 95.71 % statements |
| Frontend `npm run test:cov` | 13 | 48 | 48 | 0 | 90.26 % statements |

Las tres pruebas de defecto simulado están expresadas con `it.fails`, por lo que la suite permanece verde mientras conserva evidencia de que el mock defectuoso no satisface el comportamiento esperado.

La ejecución temporal `simulated-defects-failed.txt` contiene dos fallas reales contra mocks locales defectuosos (`EXIT_CODE=1`); el archivo de prueba temporal se eliminó después y no forma parte del cambio final.

## Archivos de evidencia

- `backend-cobertura.txt` y `frontend-cobertura.txt`: salida completa de Vitest con cobertura.
- `backend-cobertura.log` y `frontend-cobertura.log`: copias de la salida capturada.
- `cobertura/backend-coverage-summary.json` y `cobertura/frontend-coverage-summary.json`: resúmenes V8.
- `cobertura/backend-lcov.info` y `cobertura/frontend-lcov.info`: informes LCOV.
- `cobertura/backend-report.png`: captura del reporte HTML backend.
- `simulated-defects-failed.txt`: evidencia de dos pruebas fallidas por defecto simulado.

No se ejecutaron pruebas E2E, Katalon, Testomat.io ni TestLink en esta tarea; por eso no se presentan capturas ficticias.
