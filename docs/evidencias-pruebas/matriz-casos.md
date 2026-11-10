# Matriz complementaria de casos automatizados

## Contexto

LabTrack gestiona autenticación, catálogo, reservas, aprobación administrativa y devoluciones. Esta matriz complementa `docs/matriz-pruebas.md` con la evidencia ejecutada en este trabajo y separa pruebas unitarias, funcionales automatizadas, carga y sugerencias pendientes de revisión humana.

## Pruebas unitarias ejecutadas

| ID | Capa | Caso | Archivo | Resultado | Evidencia |
|---|---|---|---|---|---|
| U-01 | Backend | Reserva contigua no cruza | `backend/test/reservation-boundaries.extra.spec.ts` | Aprobado | `unitarias/backend-cobertura.txt` |
| U-02 | Backend | Duración cero es inválida | `backend/test/reservation-boundaries.extra.spec.ts` | Aprobado | `unitarias/backend-cobertura.txt` |
| U-03 | Backend | Mock que acepta duración cero | mismo archivo, `it.fails` | Falla simulada esperada | `unitarias/backend-cobertura.txt` |
| U-04 | Backend | Mock que cruza reservas contiguas | mismo archivo, `it.fails` | Falla simulada esperada | `unitarias/backend-cobertura.txt` |
| U-05 | Frontend | Límite de cuatro horas | `frontend/src/test/reservation-boundaries.extra.test.ts` | Aprobado | `unitarias/frontend-cobertura.txt` |
| U-06 | Frontend | Cierre a las 22:00 | mismo archivo | Aprobado | `unitarias/frontend-cobertura.txt` |
| U-07 | Frontend | Ventana sin duración | mismo archivo | Aprobado | `unitarias/frontend-cobertura.txt` |
| U-08 | Frontend | Mock que permite ventana sin duración | mismo archivo, `it.fails` | Falla simulada esperada | `unitarias/frontend-cobertura.txt` |

## Pruebas funcionales automatizadas

| ID | Flujo | Herramienta/ubicación | Estado |
|---|---|---|---|
| F-01 | Login y bloqueo temporal | Vitest + Supertest, `backend/test/auth.spec.ts` | Ejecutado |
| F-02 | Catálogo y filtros | Vitest + RTL, `frontend/src/test/CatalogPage.test.tsx` | Ejecutado |
| F-03 | Crear reserva y validar horario | Vitest + Supertest/RTL | Ejecutado |
| F-04 | Aprobar/rechazar solicitud | Vitest + Supertest/RTL | Ejecutado |
| F-05 | Devolución y penalización | Vitest + Supertest/RTL | Ejecutado |
| F-06 | Flujos E2E en navegador | Selenium, `frontend/e2e` | Solo referencia; no ejecutado |

## Carga y estrés

La referencia de carga y estrés está en `docs/evidencias-jmeter` y en `docs/matriz-pruebas.md`. No se rellenan resultados nuevos ni se inventan ejecuciones JMeter en esta evidencia.

## Casos sugeridos por IA

La columna de validación humana permanece pendiente deliberadamente.

| ID | Caso sugerido | Prioridad | Automatización propuesta | Validación humana |
|---|---|---|---|---|
| IA-01 | Dos reservas contiguas deben ser válidas | P1 | Backend + frontend | Pendiente de revisión |
| IA-02 | Duración cero debe rechazarse antes del envío | P1 | Frontend | Pendiente de revisión |
| IA-03 | Inicio a las 07:00 y fin a las 22:00 | P2 | Backend + frontend | Pendiente de revisión |
| IA-04 | Código de usuario con espacios y minúsculas | P2 | Backend | Pendiente de revisión |
| IA-05 | Manejo de sesión con token expirado | P1 | Backend + E2E | Diseño validado; no ejecutado; no importado a Testomat.io |

## Plantilla Katalon

Contexto: para convertir un caso de esta matriz en un caso Katalon, crear un `Test Case`, asociar datos de entrada y registrar evidencia solo después de ejecutarlo.

| Campo | Valor a completar |
|---|---|
| Test Case ID | `KAT-<ID>` |
| Nombre | Nombre del caso de la matriz |
| Precondiciones | Estado de base y sesión |
| Datos | JSON/CSV de entrada |
| Pasos | Acción, selector o endpoint, dato |
| Resultado esperado | Respuesta o estado visible |
| Resultado actual | Completar al ejecutar |
| Evidencia | Ruta de captura real |
| Estado | Not Run / Passed / Failed |

Pasos de exportación: en Katalon, abrir `Test Suite` o `Test Suite Collection`, ejecutar, revisar `Reports`, exportar el informe desde la opción de exportación disponible y conservar el archivo junto con sus capturas reales. No se agrega una captura porque Katalon no fue ejecutado.

## Plantilla Testomat.io / TestLink

Contexto: el CSV permite importar casos básicos en herramientas que acepten columnas de título, pasos, resultado esperado y estado. Ajustar el mapeo de columnas al importador elegido.

Pasos de exportación: exportar desde Testomat.io o TestLink el proyecto/suite en CSV, comparar IDs con esta matriz y guardar el reporte de ejecución. Para importar, usar el CSV incluido, mapear columnas y mantener `Pending human review` hasta que una persona valide el caso.

Archivo importable: `testomatio-import.csv`.
